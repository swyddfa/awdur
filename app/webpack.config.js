const path = require("path")
// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
const HtmlWebPackPlugin = require("html-webpack-plugin")
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const MonacoWebPackPlugin = require('monaco-editor-webpack-plugin')

const production = process.env.NODE_ENV === 'production'

module.exports = {
  mode: production ? 'production' : 'development',
  devtool: production ? '' : 'source-map',
  target: 'web',
  entry: {
    app: './src/index.ts',
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
  optimization: ((production && !process.env.CYPRESS_ENV) ? {
    splitChunks: {
      chunks: 'all'
    }
  } : undefined),
  module: {
    rules: [
      {
        test: /\.ts?$/,
        use: "ts-loader",
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
            }
          },
          {
            loader: 'postcss-loader'
          }
        ]
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
    new MiniCssExtractPlugin(),
    new MonacoWebPackPlugin({
      languages: []
    }),
  ]
}