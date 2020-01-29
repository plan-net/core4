// vue.config.js
module.exports = {
  filenameHashing: false,
  outputDir: 'dist',
  lintOnSave: true,
  publicPath: './',
  devServer: {
    port: 8084
  },
  configureWebpack: {
    resolve: {
      alias: {
        'vue$': 'vue/dist/vue.esm.js'
      }
    }
  }
}
