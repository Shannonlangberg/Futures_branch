// Metro bundler configuration for better performance
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Optimize for faster builds and lower memory usage
config.transformer = {
  ...config.transformer,
  // Reduce minification overhead in development
  minifierConfig: {
    keep_classnames: true,
    keep_fnames: true,
    mangle: {
      keep_classnames: true,
      keep_fnames: true,
    },
  },
};

// Cache configuration
config.cacheStores = [
  // Use file-based cache for better performance
];

// Reduce watcher overhead
config.watchFolders = [__dirname];

// Optimize resolver
config.resolver = {
  ...config.resolver,
  // Reduce file system lookups
  sourceExts: [...config.resolver.sourceExts, 'jsx', 'js', 'ts', 'tsx'],
};

module.exports = config;

