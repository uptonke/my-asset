/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './assets/js/**/*.js',
    './assets/css/**/*.css',
    './*.js'
  ],
  safelist: [
    'hidden', 'block', 'inline-block', 'inline-flex', 'flex', 'grid',
    'items-center', 'items-start', 'justify-between', 'justify-center',
    'text-left', 'text-right', 'text-center', 'font-bold', 'font-black', 'font-mono',
    'rounded', 'rounded-lg', 'rounded-xl', 'rounded-2xl', 'rounded-3xl', 'rounded-full',
    'border', 'shadow', 'shadow-lg', 'backdrop-blur-xl', 'transition', 'duration-300', 'duration-500',
    {
      pattern: /^(bg|text|border|ring|from|via|to)-(slate|gray|zinc|neutral|stone|red|orange|amber|yellow|green|emerald|cyan|sky|blue|indigo|purple|pink|white|black)-(50|100|200|300|400|500|600|700|800|900|950)(\/(5|10|15|20|25|30|40|50|60|70|75|80|90))?$/
    },
    {
      pattern: /^(p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|space-x|space-y)-(0|0\.5|1|1\.5|2|2\.5|3|3\.5|4|5|6|7|8|10|12|14|16|20|24)$/
    },
    {
      pattern: /^(w|h|min-w|min-h|max-w|max-h)-(full|screen|min|max|fit|0|1|2|3|4|5|6|8|10|12|16|20|24|32|40|48|56|64|80|96)$/
    },
    {
      pattern: /^(grid-cols|col-span|row-span)-(1|2|3|4|5|6|7|8|9|10|11|12)$/
    },
    {
      pattern: /^(text|leading|tracking)-(xs|sm|base|lg|xl|2xl|3xl|4xl|tight|normal|wide|wider|widest)$/
    }
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']
      },
      colors: {
        terminal: {
          bg: '#0f172a',
          panel: '#111827',
          line: 'rgba(148, 163, 184, 0.16)'
        }
      }
    }
  },
  corePlugins: {
    preflight: false
  },
  plugins: []
};
