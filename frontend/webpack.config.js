const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

// The Django server that handles the API, login/signup and admin.
const DJANGO_URL = 'http://localhost:8000';

module.exports = (env, argv) => {
    const isDevServer = Boolean(process.env.WEBPACK_SERVE);

    return {
        entry: path.resolve(__dirname, 'src/index.js'),
        output: {
            // The content hash changes whenever the code changes, so browsers
            // never keep using an old cached bundle after a deploy.
            filename: isDevServer ? 'main.js' : 'main.[contenthash].js',
            path: path.resolve(__dirname, 'build'),
            // Django serves build/ under /static/ (see STATICFILES_DIRS);
            // the dev server serves it from the root.
            publicPath: isDevServer ? '/' : '/static/',
            clean: true,
        },
        module: {
            rules: [
                {
                    test: /\.(js|jsx)$/,
                    exclude: /node_modules/,
                    use: { loader: 'babel-loader' },
                },
                {
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'],
                },
                {
                    test: /\.svg$/i,
                    type: 'asset/resource',
                },
            ],
        },
        resolve: {
            extensions: ['.js', '.jsx'],
        },
        plugins: [
            // Writes build/index.html with the right <script> tag for the
            // hashed bundle. Django serves this file for every React page.
            new HtmlWebpackPlugin({
                template: path.resolve(__dirname, 'index.html'),
            }),
        ],
        // `npm start`: http://localhost:3000 with instant reloads.
        // Everything React doesn't handle is forwarded to Django.
        devServer: {
            port: 3000,
            hot: true,
            historyApiFallback: true,
            proxy: [
                {
                    context: ['/api', '/login', '/signup', '/admin', '/static'],
                    target: DJANGO_URL,
                },
            ],
        },
    };
};
