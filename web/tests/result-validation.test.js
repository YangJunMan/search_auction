const {test}=require('node:test');const assert=require('node:assert/strict');
const {validateFirstPage}=require('../lib/result-validation');
test('does not misreport an unreadable listing page as an empty result',()=>{
 assert.throws(()=>validateFirstPage([],275),/SEARCH_RESULT_UNREADABLE/);
 assert.throws(()=>validateFirstPage([],null),/SEARCH_RESULT_UNREADABLE/);
 assert.doesNotThrow(()=>validateFirstPage([],0));
 assert.doesNotThrow(()=>validateFirstPage([{id:1}],275));
});
