const path = require('path');

module.exports = {
    entry: path.resolve(__dirname, 'src/index.js'),
    output: {
        filename: 'main.js',
        path: path.resolve(__dirname, 'build'),
        clean: true, // Clean the output directory before emit
    },
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                },
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader'],
            },
            {
            test: /\.svg$/i,
            type: 'asset/resource', // or use file-loader if you prefer
            }

        ],
    },
    resolve: {
        extensions: ['.js', '.jsx'],
    },
};