function validateFirstPage(items,total) {
  if (!items.length && total !== 0) throw new Error('SEARCH_RESULT_UNREADABLE');
}
module.exports={validateFirstPage};
