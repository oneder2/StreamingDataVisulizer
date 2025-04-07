/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class', // 使用 'dark' 类来控制暗色模式
  content: [
    // 配置 Tailwind 去扫描这些文件以查找用到的类名
    "./data_analyzer_app/static/**/*.html",
    "./data_analyzer_app/static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        // 将 Inter 设置为默认字体 (可选, Tailwind 默认字体集通常足够)
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
