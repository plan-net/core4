// vue.config.js
module.exports = {
  outputDir: 'dist',
  lintOnSave: true,
  publicPath: './',
  configureWebpack: {
    resolve: {
      alias: {
        'vue$': 'vue/dist/vue.esm.js'
      }
    }
  }
}
