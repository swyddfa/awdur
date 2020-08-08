const path = require("path")

module.exports = {
  mode: 'development',
  target: 'electron-main',
  devtool: 'source-map',
  entry: {
    app: "./src/main/main.ts",
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
