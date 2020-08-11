const path = require("path")

const production = process.env.NODE_ENV === 'production'

module.exports = {
  mode: production ? 'production' : 'development',
  devtool: production ? '' : 'source-map',
  target: 'electron-main',
  entry: {
    app: "./src/main/main.ts",
  },
  node: {
    __dirname: false
  },
  resolve: {
    extensions: [".ts", ".js"]
  },
  output: {
    filename: "main.js",
    path: path.resolve(__dirname, "dist")
  },
  module: {
    rules: [
      {
        test: /\.ts?$/,
        use: "ts-loader",
        exclude: /node_modules/
      }
    ]
  }
}
