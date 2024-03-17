function myImagePlugin(md) {
    // 保存原始的image渲染规则
    const defaultRender = md.renderer.rules.image || function(tokens, idx, options, env, self) {
        return self.renderToken(tokens, idx, options);
    };

    md.renderer.rules.image = function(tokens, idx, options, env, self) {
        const token = tokens[idx];
        const srcIndex = token.attrIndex('src');
        const src = token.attrs[srcIndex][1];
        const altIndex = token.attrIndex('alt');
        const alt = token.attrs[altIndex][1];

        let displayText = '点击查看图片'; // 默认文字
        if (src.includes('cover')) {
            displayText = '点击查看封面';
        } else if (src.includes('Screenshot')) {
            displayText = '点击查看截图';
        } else if (src.includes('.gif')) {
            displayText = '点击查看演示';
        }
        // 可以根据需要添加更多条件

        // 生成唯一ID，以确保每个图片的展示控件是唯一的
        const uniqueId = 'img_' + Math.random().toString(36).substr(2, 9);

        // 返回自定义的HTML代码
        return `
            <div id="${uniqueId}_link" style="cursor: pointer;text-decoration: underline;" onclick="document.getElementById('${uniqueId}').style.display='block'; this.style.display='none'">
                ${displayText}
            </div>
            <img id="${uniqueId}" src="${src}" alt="${alt}" style="display:none; max-width: 100%;" />
        `;
    };
}

// 在Hexo的scripts文件夹中的某个脚本文件中
hexo.extend.filter.register('markdown-it:renderer', function(md) {
    md.use(myImagePlugin);
});