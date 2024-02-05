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
      const regex = new RegExp(`${escapedTitle}($|(?=,)|\n)`, 'g');
      data.content = data.content.replace(regex, `[${title}](${url})`);
    }
  });
  return data;
});
