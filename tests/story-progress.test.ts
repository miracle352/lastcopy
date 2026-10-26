import {test} from 'node:test';
import assert from 'node:assert/strict';
test('scroll story preserves an original first frame, reaches readback and clamps overscroll',async()=>{
 const {storyProgress}=await import('../web/lib/story-progress');
 assert.equal(storyProgress(0,800,900,true),0);
 assert.equal(storyProgress(-900,800,900,true),1);
 assert.equal(storyProgress(900,1200,900),0);
 assert.equal(storyProgress(-1200,1200,900),1);
 assert(storyProgress(-200,1200,900)>.5);
});
