hexo.extend.helper.register('category_count', function(categoryName) {
    // 查找特定名称的分类
    const category = hexo.locals.get('categories').findOne({name: categoryName});
    
    // 如果找到分类，则返回其下的文章数目，否则返回0
    return category ? category.posts.length : 0;
  });