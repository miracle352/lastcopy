/** Authoring utility: requires Codex's bundled presentation runtime, not an app dependency. */
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const root=process.cwd(),home=process.env.USERPROFILE;
const runtime=path.join(home,'.cache/codex-runtimes/codex-primary-runtime/dependencies');
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const skill=path.join(home,'.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const build=path.join(root,'private/submission-final'),output=path.join(root,'submission');
await fs.mkdir(path.join(build,'previews'),{recursive:true});await fs.mkdir(output,{recursive:true});
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const colors={ink:'#060C0C',paper:'#EAF5F0',mint:'#42DBB3',blue:'#73BDF4',amber:'#F2B66D',muted:'#B7CFC4',green:'#206451'};
function text(slide,value,x,y,w,h,size=28,{serif=false,bold=false,color}={}){
 const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 shape.text=value;shape.text.style={typeface:serif?'Georgia':'Arial',fontSize:size,bold,color:color??(slide._dark?colors.paper:colors.ink)};return shape;
}
function slide(title,{dark=true,notes=''}={}){
 const s=deck.slides.add();s.background.fill=dark?colors.ink:colors.paper;s._dark=dark;
 if(title)text(s,title,70,62,1140,150,52,{serif:true});s.speakerNotes.text=notes;return s;
}
async function screenshot(s,name,x,y,w,h){const raw=await fs.readFile(path.join(root,name));s.images.add({blob:raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength),contentType:'image/png',alt:'Actual LastCopy product screenshot with synthetic evidence',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
let s=slide('',{notes:'LastCopy, Open Agent Hackathon 2026, Track 02: The Agent That Can Explain Why. Working product at https://lastcopy-five.vercel.app. No sponsor endorsement claimed.'});
text(s,'LastCopy',70,65,500,55,34,{bold:true,color:colors.mint});
text(s,'Bring every\nrecord home',70,180,1100,250,88,{serif:true});
text(s,'Check that field forms, answers and photos reached the server.\nRecover supported gaps. Verify the result.',74,480,1080,110,30);
text(s,'OPEN AGENT 2026 · TRACK 02',74,650,1080,35,21,{color:colors.muted});

s=slide('Record totals do not tell\nthe whole story',{dark:false,notes:'Authored fixture: fixtures/stage2/stranded and public /demo stranded case. Actual comparator finds two MISSING_SUBMISSION items while other records exist on the server. No field-user or adoption statistic is claimed.'});
text(s,'2',70,245,220,190,150,{serif:true,color:colors.green});
text(s,'stranded submissions in an authored control.\nOther records still exist on the server.',300,280,880,130,34);
text(s,'A spreadsheet can omit repeats while the original XML retains every answer.',70,490,1140,90,30);
text(s,'Equal file bytes do not establish that every referenced filename is accessible.',70,600,1140,70,25);

s=slide('A finding you can open',{notes:'Actual product capture: docs/verification/release-final/hosted-owner/evidence-390.png, 26 October 2026. Synthetic record. Source files, namespace-aware XML occurrence paths, values, media slot and evidence receipt are inspectable; raw inputs remain unchanged.'});
text(s,'See the original file, precise XML occurrence\nand attachment reference.',70,230,720,140,32);
text(s,'Add exports\nCheck copies\nReview gaps\nVerify recovery',70,410,690,225,30,{color:colors.mint});
await screenshot(s,'docs/verification/release-final/hosted-owner/evidence-390.png',870,155,300,510);

s=slide('The missing-answer hypothesis\nwas rejected',{dark:false,notes:'Fresh actual connected capture, 26 October 2026: private/release-connected-export-retry; independently verified in docs/verification/release-final/connected-export-independent.json. Public receipts at web/public/verification/sponsor-export-review.json. Replay on the website; no live calls while viewing. Actual model: nvidia/nemotron-3.5-lightning-30b-a3b, reported by Nightshift.'});
text(s,'Missing answers?',70,280,330,80,32,{bold:true});text(s,'→',400,280,65,80,42,{color:colors.green});
text(s,'Read raw XML',480,280,320,80,32,{bold:true});text(s,'→',805,280,65,80,42,{color:colors.green});
text(s,'Guide the export',880,280,330,100,32,{bold:true});
text(s,'The reviewer requested the original XML. Repeated answers were present, so the plan changed to export guidance.',70,435,1130,115,30);
text(s,'Captured Connected run · 4 actual Zetaris queries · 3 Nightshift calls\n2 critique rounds · World Model reads changed the next action',70,600,1140,80,24,{color:colors.green});

s=slide('Evidence directs the next step',{notes:'Architecture: docs/ARCHITECTURE.md; lastcopy/connected.py; lastcopy/investigation.py; bridge/investigation-world.ts. Small bounded CSV manifests are materialized in Zetaris NDP; no claim of heterogeneous in-place federation or cheap full-file scans from LIMIT. The pinned unchanged Apache-2.0 Meterless World Model reference is credited in THIRD_PARTY_NOTICES.md. Development used Codex desktop on Windows; Cursor was not used.'});
text(s,'Zetaris',70,235,310,65,36,{bold:true,color:colors.blue});text(s,'Scoped evidence queries\nPrivate source-object hashes',70,320,310,110,26);
text(s,'→',390,260,60,65,42,{color:colors.mint});
text(s,'World Model',470,235,350,65,36,{bold:true,color:colors.mint});text(s,'Provenance and revisions\nReads select unresolved work',470,320,350,110,26);
text(s,'→',825,260,60,65,42,{color:colors.mint});
text(s,'Nightshift',910,235,300,65,36,{bold:true,color:colors.blue});text(s,'Bounded investigator\nand reviewer inference',910,320,300,110,26);
text(s,'The deterministic verifier decides preservation.',70,495,1140,70,38,{serif:true});
text(s,'Python / FastAPI · Next.js / React · SQLite · ODK Central\nModels request evidence; they cannot alter verdicts or write field records.',70,610,1140,75,24,{color:colors.muted});

s=slide('Recovery is verified by readback',{dark:false,notes:'Real dedicated synthetic Central project 2. Original recovery and lost-acknowledgement/restart acceptance: docs/verification/cloud/restart-control-receipt.json and restart-control-events.jsonl. Fresh original XML/version/media readback on 26 October: docs/verification/release-final/recovery-summary.json (approved metadata summary; full readback retained privately on AWS). Repeated Apply was tested with transport writes forbidden; one matching instance remained. No new upload is claimed for 26 October. Source hashes retained unchanged.'});
text(s,'A missing submission was restored\nwith its original identifier.',70,225,740,130,34);
text(s,'MISSING_SUBMISSION → PRESERVED',70,380,1100,65,28,{bold:true,color:colors.green});
text(s,'1',930,225,260,150,118,{serif:true,color:colors.green});text(s,'matching instance',900,375,310,65,25);
text(s,'The upload completed before acknowledgement. After a restart,\nreadback established preservation before another write was considered.',70,490,1130,105,28);
text(s,'Upload captured 25 October · fresh XML/media checked 26 October\nRepeat Apply: no upload · originals unchanged',70,620,1130,70,24,{color:colors.green});

s=slide('Checked paths and remaining limits',{notes:'Verification receipts: docs/verification/release-final. Actual network-disabled production container compared all five fixtures with zero provider calls and unchanged source files. Both fresh sponsor cases were independently recomputed. Human confirmed signup and password-reset email/sign-in. npm full/production audits: zero known advisories; 25 Python version entries checked against PyPI: none reported. Debian base-image advisories remain open; this is not independent security certification. Lighthouse goals remain goals, not field Core Web Vitals claims.'});
text(s,'Verified',70,225,520,60,34,{bold:true,color:colors.mint});
text(s,'Offline comparisons without external network\nActual sponsor investigations and reviewer revision\nFresh Central readback; no duplicate on repeat\nSignup and password reset confirmed',70,310,540,280,27);
text(s,'Still to finish',690,225,520,60,34,{bold:true,color:colors.amber});
text(s,'Physical-phone automatic backup\nUnattended off-host and full-system recovery\nIndependent security review and retention policy\nRemaining mobile performance goals',690,310,520,280,27);
text(s,'The hosted core works while the PC is off. The local sponsor runtime and emulator still require it.',70,645,1140,50,23,{color:colors.muted});

s=slide('LastCopy',{dark:false,notes:'Review draft, not an event submission. Demo: https://lastcopy-five.vercel.app/demo. Captured sponsor receipts: https://lastcopy-five.vercel.app/technical. Repository: https://github.com/miracle352/lastcopy remains private until the owner chooses judge access/publication. Official requirements verified 26 October at https://hackathon.genai.works/event/open-agent-hackathon-2026#rules. Deadline 27 October 23:45 UTC (28 October 00:45 Africa/Lagos). Current authenticated submission form fields remain for owner review.'});
text(s,'Keep the originals.\nKeep the evidence.',70,235,1140,170,50,{serif:true,color:colors.green});
text(s,'Try without an account\nlastcopy-five.vercel.app/demo',70,460,1140,115,32);
text(s,'Next: independent device backup and stronger operational controls',70,635,1140,60,25);

for(const [index,s] of deck.slides.items.entries()){
 const image=await deck.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,'previews',`slide-${index+1}.png`),new Uint8Array(await image.arrayBuffer()));
}
const candidate=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(deck)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const final=path.join(output,'LastCopy-submission-deck.pptx');
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,explicitTotalSlideCount:8,
 pythonExecutable:path.join(runtime,'python/python.exe'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Arial','Georgia']},verifyArtifactToolImport:true,
 receiptPath:path.join(build,'validation.json')});
console.log('Created eight editable review slides:',final);
