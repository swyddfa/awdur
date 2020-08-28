const path = require("path")
// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
const HtmlWebPackPlugin = require("html-webpack-plugin")
const MonacoWebPackPlugin = require('monaco-editor-webpack-plugin')

const production = process.env.NODE_ENV === 'production'

module.exports = {
  mode: production ? 'production' : 'development',
  devtool: production ? '' : 'source-map',
  target: 'web',
  entry: {
    app: './src/index.ts'
  },
  resolve: {
    extensions: [".js", ".ts"]
  },
  devServer: {
    contentBase: path.join(__dirname, "public"),
    compress: true,
    port: 9000
  },
  output: {
    globalObject: "self",
    filename: "[name].bundle.js",
    path: path.resolve(__dirname, "public")
  },
  module: {
    rules: [
      {
        test: /\.ts?$/,
        use: "ts-loader",
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"]
      },
      {
        test: /\.ttf$/,
        use: ['file-loader']
      }
    ]
  },
  plugins: [
    //new BundleAnalyzerPlugin(),
    new HtmlWebPackPlugin({
      template: path.join("src", "index.html")
    }),
    new MonacoWebPackPlugin({
      languages: []
    })
  ]
}