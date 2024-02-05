function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

hexo.extend.filter.register('before_post_render', function(data) {
  let titleToUrlMap = {};
  hexo.locals.get('posts').data.forEach(function(post) {
    titleToUrlMap[post.title] = post.permalink;
  });

  Object.keys(titleToUrlMap).forEach(title => {
    if (data.title !== title){
      const url = titleToUrlMap[title];
      const escapedTitle = escapeRegExp(title); // 转义标题
      // 修改正则表达式，添加捕获组以捕获 \n
      const regex = new RegExp(`(${escapedTitle})($|(?=,))`, 'gm');
      // 在替换字符串中使用 $1 来引用被捕获的标题，$2 引用尾随的字符（包括 \n）
      data.content = data.content.replace(regex, `[${title}](${url})`);
    }
  });
  return data;
});
