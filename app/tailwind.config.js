module.exports = {
  purge: [
    './src/**/*.ts',
    './src/**/*.css',
    './src/**/*.html'
  ],
  future: {
    removeDeprecatedGapUtilities: true,
  },
  variants: {
    backgroundColor: ['responsive', 'hover', 'focus', 'disabled'],
  }
}