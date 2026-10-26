/** Only product-owned destinations survive sign-in; never arbitrary redirects. */
export function ownerReturn(value:unknown):string {
  return typeof value==='string'&&/^\/(?:app(?:\/new|\?sample=(?:media|stranded|export|history|conflict))?|account|integrations|runs\/[A-Za-z0-9_-]{1,128})$/.test(value)?value:'/app';
}
