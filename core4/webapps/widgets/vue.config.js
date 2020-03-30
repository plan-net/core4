// vue.config.js
module.exports = {
  filenameHashing: false,
  outputDir: 'dist',
  lintOnSave: true,
  publicPath: './',
  devServer: {
    proxy: {
      '/core4/api/v1/*': {
        target: 'http://0.0.0.0:5001',
        secure: false
      }
    },
    port: 8080
  },
  configureWebpack: {
    resolve: {
      alias: {
        vue$: 'vue/dist/vue.esm.js'
      }
    }
  }
}
