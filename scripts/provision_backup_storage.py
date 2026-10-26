"""Run in the signed-in AWS CloudShell, only after the owner's storage/IAM approval.

Creates one fixed private destination and an uploader with no delete permission.
The new key is written to a mode-0600 file, never printed or put in a receipt.
"""
import hashlib,json,os
from pathlib import Path

ACCOUNT='350353785155'
REGION='ap-southeast-1'
BUCKET='lastcopy-private-backups-350353785155-sg'
USER='lastcopy-backup-uploader'
PREFIX='daily/'


def policy():
    return {'Version':'2012-10-17','Statement':[
        {'Effect':'Allow','Action':['s3:GetBucketLocation','s3:ListBucket','s3:ListBucketVersions'],
         'Resource':'arn:aws:s3:::'+BUCKET,'Condition':{'StringLike':{'s3:prefix':[PREFIX+'*']}}},
        {'Effect':'Allow','Action':['s3:PutObject','s3:GetObject'],
         'Resource':'arn:aws:s3:::'+BUCKET+'/'+PREFIX+'*'},
        {'Effect':'Deny','Action':['s3:DeleteObject','s3:DeleteObjectVersion','s3:DeleteBucket'],
         'Resource':['arn:aws:s3:::'+BUCKET,'arn:aws:s3:::'+BUCKET+'/*']}]}


def main():
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    config=Config(connect_timeout=10,read_timeout=30,retries={'max_attempts':2})
    session=boto3.Session(region_name=REGION)
    assert session.client('sts',config=config).get_caller_identity()['Account']==ACCOUNT
    s3=session.client('s3',config=config);iam=session.client('iam',config=config)
    try:s3.head_bucket(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT)
    except ClientError as error:
        if error.response['Error']['Code'] not in ('404','NoSuchBucket'):raise
        s3.create_bucket(Bucket=BUCKET,CreateBucketConfiguration={'LocationConstraint':REGION},
            ObjectOwnership='BucketOwnerEnforced')
    s3.put_public_access_block(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT,
        PublicAccessBlockConfiguration=dict.fromkeys(['BlockPublicAcls','IgnorePublicAcls','BlockPublicPolicy','RestrictPublicBuckets'],True))
    s3.put_bucket_versioning(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT,VersioningConfiguration={'Status':'Enabled'})
    s3.put_bucket_encryption(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT,
        ServerSideEncryptionConfiguration={'Rules':[{'ApplyServerSideEncryptionByDefault':{'SSEAlgorithm':'AES256'}}]})
    s3.put_bucket_tagging(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT,Tagging={'TagSet':[{'Key':'Project','Value':'LastCopy'}]})
    s3.put_bucket_policy(Bucket=BUCKET,ExpectedBucketOwner=ACCOUNT,Policy=json.dumps({'Version':'2012-10-17','Statement':[
        {'Sid':'HTTPSOnly','Effect':'Deny','Principal':'*','Action':'s3:*',
         'Resource':['arn:aws:s3:::'+BUCKET,'arn:aws:s3:::'+BUCKET+'/*'],'Condition':{'Bool':{'aws:SecureTransport':'false'}}}]}))
    try:
        user=iam.get_user(UserName=USER)['User']
        assert any(t['Key']=='Project' and t['Value']=='LastCopy' for t in iam.list_user_tags(UserName=USER)['Tags'])
    except iam.exceptions.NoSuchEntityException:
        iam.create_user(UserName=USER,Tags=[{'Key':'Project','Value':'LastCopy'}])
    assert not iam.list_attached_user_policies(UserName=USER)['AttachedPolicies']
    assert set(iam.list_user_policies(UserName=USER)['PolicyNames']) <= {'LastCopyEncryptedBackupsOnly'}
    iam.put_user_policy(UserName=USER,PolicyName='LastCopyEncryptedBackupsOnly',PolicyDocument=json.dumps(policy()))
    path=Path.home()/'lastcopy-backup-uploader.json'
    existing=iam.list_access_keys(UserName=USER)['AccessKeyMetadata']
    if existing:
        if not path.is_file():raise ValueError('An uploader key already exists; do not create another')
    else:
        key=iam.create_access_key(UserName=USER)['AccessKey']
        raw={'bucket':BUCKET,'region':REGION,'account':ACCOUNT,'prefix':PREFIX,
             'access_key_id':key['AccessKeyId'],'secret_access_key':key['SecretAccessKey']}
        descriptor=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'w') as output:json.dump(raw,output)
    print(json.dumps({'status':'configured','bucket':BUCKET,'region':REGION,'uploader':USER,
        'public_access_blocked':True,'versioning':True,'delete_permission':False,
        'policy_sha256':hashlib.sha256(json.dumps(policy(),sort_keys=True).encode()).hexdigest(),
        'credential_file':'~/lastcopy-backup-uploader.json','credentials_printed':False}))


if __name__=='__main__':main()
