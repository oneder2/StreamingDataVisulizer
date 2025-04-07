// static/script.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM fully loaded and parsed"); // 确认DOM加载完成

    // --- State Management (状态管理) ---
    const state = {
        filename: null,             // 当前文件名
        columnsInfo: [],            // 列信息数组 {name: string, type: string}
        selectedColumn: null,       // 当前选中的列 {name: string, type: string}
        isLoading: false,           // 是否正在加载
        currentWeightColumn: '',    // 当前用于加权的列名
        barChartInstance: null,     // 条形图实例
        pieChartInstance: null,     // 饼图实例
        messageTimeout: null,       // 消息提示框的超时计时器
        currentRankingPage: 1,      // 当前排行榜页码
        totalRankedItems: 0,        // 排行榜总项目数
        rankingPageSize: 10,        // 排行榜每页大小
        currentRankingType: null,   // 当前排行榜类型: 'artists' 或 'songs'
        isDarkMode: false           // 当前是否为暗色模式
    };

    // --- DOM Elements (DOM元素缓存) ---
    const dom = {
        html: document.documentElement,
        darkModeToggle: document.getElementById('darkModeToggle'),
        fileInput: document.getElementById('fileInput'),
        fileNameDisplay: document.getElementById('fileNameDisplay'),
        columnList: document.getElementById('columnList'),
        weightColumnSelect: document.getElementById('weightColumnSelect'),
        analyzeArtistsBtn: document.getElementById('analyzeArtistsBtn'),
        analyzeSongsBtn: document.getElementById('analyzeSongsBtn'),
        singleColumnAnalysisArea: document.getElementById('singleColumnAnalysisArea'),
        rankingAnalysisArea: document.getElementById('rankingAnalysisArea'),
        numericDisplayArea: document.getElementById('numericDisplayArea'),
        booleanDisplayArea: document.getElementById('booleanDisplayArea'),
        noDataDisplayArea: document.getElementById('noDataDisplayArea'),
        analysisTitle: document.getElementById('analysisTitle'),
        barChartTitle: document.getElementById('barChartTitle'),
        pieChartTitle: document.getElementById('pieChartTitle'),
        rankingTitle: document.getElementById('rankingTitle'),
        rankingContent: document.getElementById('rankingContent'),
        noDataMessage: document.getElementById('noDataMessage'),
        messageBox: document.getElementById('messageBox'),
        loadingOverlay: document.getElementById('loadingOverlay'),
        loadMoreArtistsBtn: document.getElementById('loadMoreArtistsBtn'),
        loadMoreSongsBtn: document.getElementById('loadMoreSongsBtn'),
        statElements: {
            mean: document.getElementById('stat_mean'), variance: document.getElementById('stat_variance'),
            std: document.getElementById('stat_std'), min: document.getElementById('stat_min'),
            q1: document.getElementById('stat_q1'), median: document.getElementById('stat_median'),
            q3: document.getElementById('stat_q3'), max: document.getElementById('stat_max'),
            count: document.getElementById('stat_count')
        },
        chartExportButtonsContainer: document.getElementById('chartExportButtons'),
        exportBarChartBtn: document.getElementById('exportBarChartBtn'),
        exportPieChartBtn: document.getElementById('exportPieChartBtn'),
        tableExportButtonsContainer: document.getElementById('tableExportButtons'),
        exportTableCsvBtn: document.getElementById('exportTableCsvBtn'),
        exportTableXlsxBtn: document.getElementById('exportTableXlsxBtn'),
    };

    // --- Constants (常量定义) ---
    const API_ENDPOINTS = { // API端点
        UPLOAD: '/upload', // main_bp 注册时没有前缀
        // analysis_bp 注册时有 /analyze 前缀
        SINGLE_COLUMN_DATA: '/analyze/data',
        ARTIST_ANALYSIS: '/analyze/top_artists',
        SONG_ANALYSIS: '/analyze/top_songs',
        // 修改: 添加 /analyze 前缀
        EXPORT_RANKING: '/analyze/export/ranking'
    };
    const SINGLE_COLUMN_VIEW_STATES = { /* ... (保持不变) ... */
        INITIAL: 'initial', NUMERIC: 'numeric', BOOLEAN: 'boolean', NO_DATA: 'noData', ERROR: 'error'
    };
    const RANKING_TYPE = { ARTISTS: 'artists', SONGS: 'songs' };
    const THEME = { LIGHT: 'light', DARK: 'dark' };

    // --- Utility Functions (工具函数) ---
    function formatNumber(num, decimals = 2) { /* ... (保持不变) ... */
        if (num === null || typeof num === 'undefined' || isNaN(num)) return 'N/A';
        if (Math.abs(num) > 0 && Math.abs(num) < 0.01) return num.toExponential(decimals);
        if (Math.abs(num - Math.round(num)) < 1e-9) return Math.round(num).toLocaleString();
        return num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
    }

    // --- UI Update Functions (UI更新函数) ---
    // ... (setLoadingState, showMessage, updateFileNameDisplay, populateColumnList, populateWeightDropdown, updateStatsDisplay, renderArtistTable, renderSongTable, switchSingleColumnView, resetUIComponents 不变) ...
    function setLoadingState(loading, button = null) { /* ... (保持不变) ... */ state.isLoading = loading; dom.loadingOverlay.style.display = loading ? 'flex' : 'none'; if (button) { button.disabled = loading; if(loading && !button.dataset.originalText) { button.dataset.originalText = button.textContent; button.textContent = 'Loading...'; } else if (!loading && button.dataset.originalText) { button.textContent = button.dataset.originalText; button.removeAttribute('data-original-text'); } } }
    function showMessage(message, type = 'success', duration = 3000) { /* ... (保持不变) ... */ if (state.messageTimeout) clearTimeout(state.messageTimeout); dom.messageBox.textContent = message; dom.messageBox.className = 'fixed bottom-5 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-md text-white shadow-lg text-sm z-[1000] opacity-0 pointer-events-none transition-opacity duration-300 ease-in-out'; if (type === 'success') dom.messageBox.classList.add('bg-green-600'); else if (type === 'error') dom.messageBox.classList.add('bg-red-600'); else dom.messageBox.classList.add('bg-blue-600'); requestAnimationFrame(() => { dom.messageBox.classList.add('show'); }); state.messageTimeout = setTimeout(() => { dom.messageBox.classList.remove('show'); }, duration); }
    function updateFileNameDisplay(filename) { /* ... (保持不变) ... */ dom.fileNameDisplay.textContent = filename ? `File: ${filename}` : 'No file selected.'; }
    function populateColumnList(columns) { /* ... (保持不变) ... */ dom.columnList.innerHTML = ''; if (!columns || columns.length === 0) { dom.columnList.innerHTML = '<li class="p-3 text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-700/50 rounded-md">No analyzable columns found.</li>'; return; } columns.forEach((colInfo, index) => { const li = document.createElement('li'); li.className = 'column-item p-3 text-sm flex justify-between items-center bg-white dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-gray-700 hover:text-blue-700 dark:hover:text-blue-300'; if (index === 0) li.classList.add('rounded-t-md'); if (index === columns.length - 1) li.classList.add('border-b-0', 'rounded-b-md'); li.dataset.columnName = colInfo.name; li.dataset.columnType = colInfo.type; const nameSpan = document.createElement('span'); nameSpan.textContent = colInfo.name; nameSpan.className = "truncate mr-2"; const typeSpan = document.createElement('span'); typeSpan.textContent = `(${colInfo.type})`; typeSpan.className = 'column-type flex-shrink-0 text-xs bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 px-1.5 py-0.5 rounded-sm'; li.appendChild(nameSpan); li.appendChild(typeSpan); li.addEventListener('click', handleSingleColumnSelection); dom.columnList.appendChild(li); }); }
    function populateWeightDropdown(columns) { /* ... (保持不变) ... */ dom.weightColumnSelect.innerHTML = '<option value="">-- No Weighting --</option>'; if (!columns) { dom.weightColumnSelect.disabled = true; return; } const numericColumns = columns.filter(col => col.type === 'int' || col.type === 'float'); if (numericColumns.length > 0) { numericColumns.forEach(colInfo => { const option = document.createElement('option'); option.value = colInfo.name; option.textContent = colInfo.name; dom.weightColumnSelect.appendChild(option); }); dom.weightColumnSelect.disabled = false; } else { dom.weightColumnSelect.disabled = true; } }
    function updateStatsDisplay(stats) { /* ... (保持不变) ... */ for (const key in dom.statElements) { dom.statElements[key].textContent = stats.hasOwnProperty(key) ? formatNumber(stats[key]) : 'N/A'; } }
    function renderArtistTable(artistData, append = false) { /* ... (保持不变) ... */ const container = dom.rankingContent; let table = container.querySelector('table'); let tbody = table ? table.querySelector('tbody') : null; if (!append || !table || !tbody || state.currentRankingType !== RANKING_TYPE.ARTISTS) { container.innerHTML = ''; if (!artistData || artistData.length === 0) { container.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">No artist ranking data available.</p>'; return; } table = document.createElement('table'); table.className = 'min-w-full divide-y divide-gray-200 dark:divide-gray-600 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm'; const thead = document.createElement('thead'); thead.className = 'bg-gray-50 dark:bg-gray-700'; thead.innerHTML = `<tr><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Rank</th><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Artist</th><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Top Track</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Avg Popularity</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Avg Loudness</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Score</th></tr>`; table.appendChild(thead); tbody = document.createElement('tbody'); tbody.className = 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600'; table.appendChild(tbody); container.appendChild(table); } artistData.forEach((artist, index) => { const tr = document.createElement('tr'); const baseIndex = append ? (state.currentRankingPage - 2) * state.rankingPageSize + index : index; tr.className = baseIndex % 2 === 0 ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60' : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'; tr.innerHTML = `<td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700 dark:text-gray-300 text-center w-16 rank-col">${artist.rank}</td><td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">${artist.artist || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">${artist.top_track || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.avg_popularity, 1)}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.avg_loudness, 1)}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.score, 3)}</td>`; tbody.appendChild(tr); }); }
    function renderSongTable(songData, append = false) { /* ... (保持不变) ... */ const container = dom.rankingContent; let table = container.querySelector('table'); let tbody = table ? table.querySelector('tbody') : null; if (!append || !table || !tbody || state.currentRankingType !== RANKING_TYPE.SONGS) { container.innerHTML = ''; if (!songData || songData.length === 0) { container.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">No song ranking data available.</p>'; return; } table = document.createElement('table'); table.className = 'min-w-full divide-y divide-gray-200 dark:divide-gray-600 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm'; const thead = document.createElement('thead'); thead.className = 'bg-gray-50 dark:bg-gray-700'; thead.innerHTML = `<tr><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Rank</th><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Title</th><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Artist(s)</th><th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Album</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Popularity</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Loudness</th><th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Score</th></tr>`; table.appendChild(thead); tbody = document.createElement('tbody'); tbody.className = 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600'; table.appendChild(tbody); container.appendChild(table); } songData.forEach((song, index) => { const tr = document.createElement('tr'); const baseIndex = append ? (state.currentRankingPage - 2) * state.rankingPageSize + index : index; tr.className = baseIndex % 2 === 0 ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60' : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'; tr.innerHTML = `<td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700 dark:text-gray-300 text-center w-16 rank-col">${song.rank}</td><td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">${song.name || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">${song.artists || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">${song.album || 'N/A'}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.popularity, 1)}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.loudness, 1)}</td><td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.score, 3)}</td>`; tbody.appendChild(tr); }); }
    function switchSingleColumnView(viewType, message = '') { /* ... (保持不变) ... */ dom.singleColumnAnalysisArea.style.display = 'flex'; dom.numericDisplayArea.style.display = 'none'; dom.booleanDisplayArea.style.display = 'none'; dom.noDataDisplayArea.style.display = 'none'; if (dom.chartExportButtonsContainer) dom.chartExportButtonsContainer.style.display = 'none'; if (dom.exportBarChartBtn) dom.exportBarChartBtn.style.display = 'none'; if (dom.exportPieChartBtn) dom.exportPieChartBtn.style.display = 'none'; switch (viewType) { case SINGLE_COLUMN_VIEW_STATES.INITIAL: dom.noDataDisplayArea.style.display = 'flex'; dom.noDataMessage.textContent = 'Select a column for analysis.'; dom.analysisTitle.textContent = 'Single Column Analysis'; break; case SINGLE_COLUMN_VIEW_STATES.NUMERIC: dom.numericDisplayArea.style.display = 'grid'; if (dom.chartExportButtonsContainer) dom.chartExportButtonsContainer.style.display = 'flex'; if (dom.exportBarChartBtn) dom.exportBarChartBtn.style.display = 'inline-block'; break; case SINGLE_COLUMN_VIEW_STATES.BOOLEAN: dom.booleanDisplayArea.style.display = 'flex'; if (dom.chartExportButtonsContainer) dom.chartExportButtonsContainer.style.display = 'flex'; if (dom.exportPieChartBtn) dom.exportPieChartBtn.style.display = 'inline-block'; break; case SINGLE_COLUMN_VIEW_STATES.NO_DATA: case SINGLE_COLUMN_VIEW_STATES.ERROR: dom.noDataDisplayArea.style.display = 'flex'; dom.noDataMessage.textContent = message || 'No data available or an error occurred.'; dom.analysisTitle.textContent = viewType === SINGLE_COLUMN_VIEW_STATES.ERROR ? 'Analysis Error' : 'Single Column Analysis'; break; default: console.warn("Unknown single column view state:", viewType); dom.noDataDisplayArea.style.display = 'flex'; dom.noDataMessage.textContent = 'An unexpected view state occurred.'; dom.analysisTitle.textContent = 'Error'; break; } }
    function resetUIComponents() { /* ... (保持不变) ... */ populateColumnList([]); populateWeightDropdown([]); dom.weightColumnSelect.disabled = true; dom.weightColumnSelect.value = ''; dom.weightColumnSelect.removeAttribute('data-previous-weight'); dom.analyzeArtistsBtn.disabled = true; dom.analyzeSongsBtn.disabled = true; updateFileNameDisplay(null); resetBarChart(); resetPieChart(); state.selectedColumn = null; state.currentWeightColumn = ''; document.querySelectorAll('#columnList .column-item.selected').forEach(item => item.classList.remove('selected', 'bg-blue-100', 'dark:bg-blue-900')); dom.rankingAnalysisArea.style.display = 'none'; dom.rankingContent.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">Click an analysis button above.</p>'; dom.loadMoreArtistsBtn.style.display = 'none'; dom.loadMoreSongsBtn.style.display = 'none'; state.currentRankingPage = 1; state.totalRankedItems = 0; state.currentRankingType = null; switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.INITIAL); if (dom.chartExportButtonsContainer) dom.chartExportButtonsContainer.style.display = 'none'; if (dom.exportBarChartBtn) dom.exportBarChartBtn.style.display = 'none'; if (dom.exportPieChartBtn) dom.exportPieChartBtn.style.display = 'none'; if (dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'none'; }
    /** 渲染艺术家排行榜表格 (修改: 添加 Top 50 歌曲信息列) */
    function renderArtistTable(artistData, append = false) {
        const container = dom.rankingContent;
        let table = container.querySelector('table');
        let tbody = table ? table.querySelector('tbody') : null;

        if (!append || !table || !tbody || state.currentRankingType !== RANKING_TYPE.ARTISTS) {
            container.innerHTML = '';
            if (!artistData || artistData.length === 0) {
                container.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">No artist ranking data available.</p>';
                return;
            }
            table = document.createElement('table');
            table.className = 'min-w-full divide-y divide-gray-200 dark:divide-gray-600 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm';
            const thead = document.createElement('thead');
            thead.className = 'bg-gray-50 dark:bg-gray-700';
            // 表头保持不变 (使用统一化后的版本)
            thead.innerHTML = `<tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Rank</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Artist</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Top 50 Songs (Rank)</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Avg Popularity</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Avg Loudness</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Score</th>
            </tr>`;
            table.appendChild(thead);
            tbody = document.createElement('tbody');
            tbody.className = 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600';
            table.appendChild(tbody);
            container.appendChild(table);
        }

        artistData.forEach((artist, index) => {
            const tr = document.createElement('tr');
            const baseIndex = append ? (state.currentRankingPage - 2) * state.rankingPageSize + index : index;
            tr.className = baseIndex % 2 === 0 ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60' : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700';
            // 修改: 为 top_songs_info 添加 text-sm 类
            tr.innerHTML = `
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700 dark:text-gray-300 text-center w-16 rank-col">${artist.rank}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">${artist.artist || 'N/A'}</td>
                <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    <span class="text-sm">${artist.top_songs_info || '-'}</span> </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.avg_popularity, 1)}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.avg_loudness, 1)}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(artist.score, 3)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    /** 渲染歌曲排行榜表格 (修改: 调整交叉引用列字体大小) */
    function renderSongTable(songData, append = false) {
        const container = dom.rankingContent;
        let table = container.querySelector('table');
        let tbody = table ? table.querySelector('tbody') : null;

        if (!append || !table || !tbody || state.currentRankingType !== RANKING_TYPE.SONGS) {
            container.innerHTML = '';
            if (!songData || songData.length === 0) {
                container.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">No song ranking data available.</p>';
                return;
            }
            table = document.createElement('table');
            table.className = 'min-w-full divide-y divide-gray-200 dark:divide-gray-600 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm';
            const thead = document.createElement('thead');
            thead.className = 'bg-gray-50 dark:bg-gray-700';
            // 表头保持不变 (使用统一化后的版本)
            thead.innerHTML = `<tr>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Rank</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Title</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Artist(s) (Top 50 Rank)</th>
                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider">Album</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Popularity</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Loudness</th>
                <th scope="col" class="px-4 py-3 text-right text-xs font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider metric-col">Score</th>
            </tr>`;
            table.appendChild(thead);
            tbody = document.createElement('tbody');
            tbody.className = 'bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600';
            table.appendChild(tbody);
            container.appendChild(table);
        }

        songData.forEach((song, index) => {
            const tr = document.createElement('tr');
            const baseIndex = append ? (state.currentRankingPage - 2) * state.rankingPageSize + index : index;
            tr.className = baseIndex % 2 === 0 ? 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60' : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700';
            // 修改: 为 artist_ranks_info 添加 text-sm 类
            tr.innerHTML = `
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-700 dark:text-gray-300 text-center w-16 rank-col">${song.rank}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">${song.name || 'N/A'}</td>
                <td class="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
                    <span class="text-sm">${song.artist_ranks_info || song.artists || 'N/A'}</span> </td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">${song.album || 'N/A'}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.popularity, 1)}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.loudness, 1)}</td>
                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400 text-right metric-col">${formatNumber(song.score, 3)}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // --- Chart Management (图表管理) ---
    // ... (initCharts, initializeBarChart, initializePieChart, updateBarChart, updatePieChart, resetBarChart, resetPieChart 不变) ...
    function initCharts() { initializeBarChart(); initializePieChart(); }
    function initializeBarChart() {
        const ctx = document.getElementById('dataChart').getContext('2d');
        if (state.barChartInstance) state.barChartInstance.destroy();
        state.barChartInstance = new Chart(ctx, {
            type: 'bar',
            data: { labels: [], datasets: [{ label: 'Frequency', data: [], backgroundColor: 'rgba(59, 130, 246, 0.5)', borderColor: 'rgba(59, 130, 246, 1)', borderWidth: 1 }] },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Frequency', font: { size: 14 } }, // 增大 Y 轴标题字体
                        ticks: { font: { size: 12 } } // 增大 Y 轴刻度字体
                    },
                    x: {
                        title: { display: true, text: 'Value Range', font: { size: 14 } }, // 增大 X 轴标题字体
                        ticks: { font: { size: 12 } } // 增大 X 轴刻度字体
                    }
                },
                plugins: {
                    legend: { display: false }, // 通常条形图不显示图例
                    tooltip: {
                        titleFont: { size: 14 }, // 增大提示框标题字体
                        bodyFont: { size: 12 } // 增大提示框内容字体
                    }
                }
            }
        });
         // 初始应用主题颜色 (字体大小已在上面设置)
        if(state.isDarkMode !== undefined) updateChartTheme(state.barChartInstance);
    }
    function initializePieChart() {
        const ctx = document.getElementById('pieChart').getContext('2d');
        if (state.pieChartInstance) state.pieChartInstance.destroy();
        state.pieChartInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['True', 'False'],
                datasets: [{
                    label: 'Count', data: [0, 0],
                    backgroundColor: ['rgba(34, 197, 94, 0.7)', 'rgba(239, 68, 68, 0.7)'],
                    borderColor: ['rgba(22, 163, 74, 1)', 'rgba(220, 38, 38, 1)'], borderWidth: 1
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            font: { size: 14 } // 增大图例字体
                        }
                    },
                    tooltip: {
                        titleFont: { size: 14 }, // 增大提示框标题字体
                        bodyFont: { size: 12 }, // 增大提示框内容字体
                        callbacks: {
                            label: function(context) { /* ... (回调函数不变) ... */ }
                        }
                    }
                }
            }
        });
        // 初始应用主题颜色 (字体大小已在上面设置)
        if(state.isDarkMode !== undefined) updateChartTheme(state.pieChartInstance);
    }
    function updateBarChart(colName, histogram, weightedBy) {
        const chart = state.barChartInstance; dom.barChartTitle.textContent = `Histogram for "${colName}"`;
        if (chart && histogram) { chart.data.labels = histogram.labels; chart.data.datasets[0].data = histogram.values; chart.data.datasets[0].label = weightedBy ? `Weighted Frequency (${colName})` : `Frequency (${colName})`; if(chart.options.scales.x.title) chart.options.scales.x.title.text = `${colName} Value Range`; if(chart.options.scales.y.title) chart.options.scales.y.title.text = weightedBy ? 'Sum of Weights' : 'Frequency'; updateChartTheme(chart); chart.update(); } else { console.error("Bar chart instance or histogram data missing for update."); resetBarChart(); }
   }
   function updatePieChart(colName, counts, weightedBy) {
        const chart = state.pieChartInstance; dom.pieChartTitle.textContent = `Distribution for "${colName}"`;
        if (chart && counts) { const trueCount = counts.true || 0; const falseCount = counts.false || 0; chart.data.datasets[0].data = [trueCount, falseCount]; chart.data.datasets[0].label = weightedBy ? 'Weighted Proportion' : 'Count'; chart.data.labels = [`True: ${formatNumber(trueCount)}`, `False: ${formatNumber(falseCount)}`]; updateChartTheme(chart); chart.update(); } else { console.error("Pie chart instance or counts data missing for update."); resetPieChart(); }
   }
    function resetBarChart() { /* ... (保持不变) ... */ if (state.barChartInstance) { state.barChartInstance.data.labels = []; state.barChartInstance.data.datasets[0].data = []; if(state.barChartInstance.options.scales.x.title) state.barChartInstance.options.scales.x.title.text = 'Value Range'; if(state.barChartInstance.options.scales.y.title) state.barChartInstance.options.scales.y.title.text = 'Frequency'; updateChartTheme(state.barChartInstance); state.barChartInstance.update(); dom.barChartTitle.textContent = 'Histogram'; } }
    function resetPieChart() { /* ... (保持不变) ... */ if (state.pieChartInstance) { state.pieChartInstance.data.labels = ['True', 'False']; state.pieChartInstance.data.datasets[0].data = [0, 0]; updateChartTheme(state.pieChartInstance); state.pieChartInstance.update(); dom.pieChartTitle.textContent = 'Boolean Distribution'; } }


    // --- Theme Management (主题管理) ---
    // ... (updateChartTheme, applyInitialTheme, toggleDarkMode 不变) ...
     function updateChartTheme(chartInstance) { /* ... (保持不变) ... */ if (!chartInstance || !chartInstance.options) return; const isDark = state.isDarkMode; const gridColor = isDark ? 'rgba(75, 85, 99, 0.4)' : 'rgba(209, 213, 219, 0.4)'; const tickColor = isDark ? '#9ca3af' : '#6b7280'; const labelColor = isDark ? '#d1d5db' : '#374151'; const tooltipBg = isDark ? '#374151' : '#f9fafb'; const tooltipColor = isDark ? '#f9fafb' : '#1f2937'; try { if (chartInstance.options.scales) { if (chartInstance.options.scales.x) { if(chartInstance.options.scales.x.grid) chartInstance.options.scales.x.grid.color = gridColor; if(chartInstance.options.scales.x.grid) chartInstance.options.scales.x.grid.borderColor = tickColor; if(chartInstance.options.scales.x.ticks) chartInstance.options.scales.x.ticks.color = tickColor; if(chartInstance.options.scales.x.title) chartInstance.options.scales.x.title.color = labelColor; } if (chartInstance.options.scales.y) { if(chartInstance.options.scales.y.grid) chartInstance.options.scales.y.grid.color = gridColor; if(chartInstance.options.scales.y.grid) chartInstance.options.scales.y.grid.borderColor = tickColor; if(chartInstance.options.scales.y.ticks) chartInstance.options.scales.y.ticks.color = tickColor; if(chartInstance.options.scales.y.title) chartInstance.options.scales.y.title.color = labelColor; } } if (chartInstance.options.plugins?.legend?.labels) { chartInstance.options.plugins.legend.labels.color = labelColor; } if (chartInstance.options.plugins?.tooltip) { chartInstance.options.plugins.tooltip.backgroundColor = tooltipBg; chartInstance.options.plugins.tooltip.titleColor = tooltipColor; chartInstance.options.plugins.tooltip.bodyColor = tooltipColor; } } catch (error) { console.error(`Error updating theme for chart ${chartInstance.id}:`, error, "Chart options:", chartInstance.options); } }
    function applyInitialTheme() { /* ... (保持不变) ... */ console.log("Applying initial theme..."); try { const storedTheme = localStorage.getItem('theme'); const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches; state.isDarkMode = (storedTheme === THEME.DARK || (!storedTheme && systemPrefersDark)); console.log(`Stored theme: ${storedTheme}, System prefers dark: ${systemPrefersDark}, Setting dark mode to: ${state.isDarkMode}`); if (state.isDarkMode) dom.html.classList.add('dark'); else dom.html.classList.remove('dark'); if (state.barChartInstance) { updateChartTheme(state.barChartInstance); state.barChartInstance.update('none'); } if (state.pieChartInstance) { updateChartTheme(state.pieChartInstance); state.pieChartInstance.update('none'); } console.log("Initial theme applied and charts updated."); } catch (error) { console.error("Error applying initial theme:", error); } }
    function toggleDarkMode() { /* ... (保持不变) ... */ console.log("Dark mode toggle triggered. Current state:", state.isDarkMode); try { state.isDarkMode = !state.isDarkMode; console.log("New dark mode state:", state.isDarkMode); dom.html.classList.toggle('dark', state.isDarkMode); void document.body.offsetHeight; localStorage.setItem('theme', state.isDarkMode ? THEME.DARK : THEME.LIGHT); console.log("Theme class toggled and preference saved."); console.log("Updating chart themes after toggle..."); if (state.barChartInstance) { updateChartTheme(state.barChartInstance); state.barChartInstance.update('none'); console.log("Bar chart theme updated."); } if (state.pieChartInstance) { updateChartTheme(state.pieChartInstance); state.pieChartInstance.update('none'); console.log("Pie chart theme updated."); } console.log("Chart themes update process finished."); } catch (error) { console.error("Error toggling dark mode:", error); } }


    // --- API Call Functions (API调用函数) ---
    // ... (uploadFile, fetchSingleColumnData, fetchArtistRankingData, fetchTopSongData 不变) ...
    async function uploadFile(file) { /* ... (保持不变) ... */ const formData = new FormData(); formData.append('file', file); const response = await fetch(API_ENDPOINTS.UPLOAD, { method: 'POST', body: formData }); let data; try { data = await response.json(); } catch (e) { throw new Error(`Server returned non-JSON response (Status: ${response.status}). Check server logs.`); } if (!response.ok) throw new Error(data.error || `HTTP error! status: ${response.status}`); if (!data.columns || !data.filename) throw new Error(data.error || 'Invalid response from upload endpoint.'); return data; }
    async function fetchSingleColumnData(filename, colName, weightCol) { /* ... (保持不变) ... */ let fetchUrl = `${API_ENDPOINTS.SINGLE_COLUMN_DATA}?file=${encodeURIComponent(filename)}&col=${encodeURIComponent(colName)}`; if (weightCol) fetchUrl += `&weight_col=${encodeURIComponent(weightCol)}`; const response = await fetch(fetchUrl); const contentType = response.headers.get('content-type'); if (contentType && contentType.includes('application/json')) { const data = await response.json(); if (!response.ok) throw new Error(data.error || `HTTP error! status: ${response.status}`); return data; } else { const text = await response.text(); console.error("Received non-JSON response:", text); throw new Error(`Server returned non-JSON response (Status: ${response.status}). Check server logs.`); } }
    async function fetchArtistRankingData(filename, page = 1, pageSize = 10) { /* ... (保持不变) ... */ const fetchUrl = `${API_ENDPOINTS.ARTIST_ANALYSIS}?file=${encodeURIComponent(filename)}&page=${page}&page_size=${pageSize}`; const response = await fetch(fetchUrl); const contentType = response.headers.get('content-type'); if (contentType && contentType.includes('application/json')) { const data = await response.json(); if (!response.ok) throw new Error(data.error || `HTTP error! status: ${response.status}`); if (typeof data !== 'object' || !Array.isArray(data.artists) || typeof data.total_artists !== 'number') { throw new Error('Invalid data structure received for artist ranking.'); } return data; } else { const text = await response.text(); console.error("Received non-JSON response for artist ranking:", text); throw new Error(`Server returned non-JSON response for artist ranking (Status: ${response.status}).`); } }
        /** 修改: fetchTopSongData 现在获取包含交叉引用的数据 */
        async function fetchTopSongData(filename, page = 1, pageSize = 10) {
            // URL 保持不变, 后端 /top_songs 路由现在会返回增强的数据
        const fetchUrl = `${API_ENDPOINTS.SONG_ANALYSIS}?file=${encodeURIComponent(filename)}&page=${page}&page_size=${pageSize}`;
        const response = await fetch(fetchUrl);
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || `HTTP error! status: ${response.status}`);
                // 验证新字段是否存在 (可选)
                if (data.songs && data.songs.length > 0 && typeof data.songs[0].artist_ranks_info === 'undefined') {
                    console.warn("Received song data might be missing 'artist_ranks_info' field.");
            }
            if (typeof data !== 'object' || !Array.isArray(data.songs) || typeof data.total_songs !== 'number') {
                throw new Error('Invalid data structure received for song ranking.');
            }
            return data;
        } else {
            const text = await response.text();
            console.error("Received non-JSON response for song ranking:", text);
            throw new Error(`Server returned non-JSON response for song ranking (Status: ${response.status}).`);
        }
    }


    // --- Event Handlers (事件处理函数) ---
    // ... (handleFileUpload, handleSingleColumnSelection, handleWeightChange, handleArtistAnalysis, handleSongAnalysis, handleLoadMoreArtists, handleLoadMoreSongs 不变) ...
    async function handleFileUpload(event) { /* ... (保持不变) ... */ const file = event.target.files[0]; if (!file) return; resetApp(); setLoadingState(true); updateFileNameDisplay(`Uploading: ${file.name}`); try { const data = await uploadFile(file); state.filename = data.filename; state.columnsInfo = data.columns; updateFileNameDisplay(state.filename); populateColumnList(state.columnsInfo); populateWeightDropdown(state.columnsInfo); dom.analyzeArtistsBtn.disabled = false; dom.analyzeSongsBtn.disabled = false; showMessage('File uploaded successfully. Select a column or analyze rankings.', 'success'); } catch (error) { console.error('Upload error:', error); showMessage(`Upload failed: ${error.message}`, 'error'); resetApp(); } finally { setLoadingState(false); dom.fileInput.value = ''; } }
    async function handleSingleColumnSelection(event) { /* ... (保持不变) ... */ if (state.isLoading || !state.filename) return; const selectedLi = event.currentTarget; const colName = selectedLi.dataset.columnName; const colType = selectedLi.dataset.columnType; const selectedColInfo = { name: colName, type: colType }; const weightCol = dom.weightColumnSelect.value; if (state.selectedColumn && selectedColInfo.name === state.selectedColumn.name && weightCol === state.currentWeightColumn) { return; } setLoadingState(true); state.selectedColumn = selectedColInfo; state.currentWeightColumn = weightCol; document.querySelectorAll('#columnList .column-item').forEach(item => item.classList.remove('selected', 'bg-blue-100', 'dark:bg-blue-900')); selectedLi.classList.add('selected', 'bg-blue-100', 'dark:bg-blue-900'); dom.analysisTitle.textContent = `Loading analysis for "${colName}"...`; if (weightCol) dom.analysisTitle.textContent += ` (Weighted by ${weightCol})`; switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.INITIAL); try { const data = await fetchSingleColumnData(state.filename, colName, weightCol); dom.analysisTitle.textContent = `Single Column Analysis for "${colName}"`; if (data.weighted_by) dom.analysisTitle.textContent += ` (Weighted by ${data.weighted_by})`; if (data.type === 'numeric') { switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.NUMERIC); updateStatsDisplay(data.stats); updateBarChart(colName, data.histogram, data.weighted_by); } else if (data.type === 'boolean') { switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.BOOLEAN); updatePieChart(colName, data.counts, data.weighted_by); } else if (data.type === 'empty') { switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.NO_DATA, data.message || `No analyzable data found for "${colName}".`); showMessage(data.message || `No analyzable data found for "${colName}".`, 'info'); } else { throw new Error(data.error || 'Received unknown data type from server.'); } } catch (error) { console.error('Single column data fetch error:', error); showMessage(`Failed to load data for "${colName}": ${error.message}`, 'error'); switchSingleColumnView(SINGLE_COLUMN_VIEW_STATES.ERROR, `Error loading data for "${colName}".`); selectedLi.classList.remove('selected', 'bg-blue-100', 'dark:bg-blue-900'); state.selectedColumn = null; state.currentWeightColumn = ''; } finally { setLoadingState(false); } }
    function handleWeightChange() { /* ... (保持不变) ... */ if (state.selectedColumn && dom.weightColumnSelect.value !== state.currentWeightColumn) { const selectedLi = dom.columnList.querySelector(`.column-item[data-column-name="${state.selectedColumn.name}"]`); if (selectedLi) { console.log("Weight changed, re-analyzing selected column:", state.selectedColumn.name); handleSingleColumnSelection({ currentTarget: selectedLi }); } } }
    async function handleArtistAnalysis() { /* ... (保持不变) ... */ if (state.isLoading || !state.filename) { showMessage('Please upload a file first.', 'error'); return; } setLoadingState(true, dom.analyzeArtistsBtn); state.currentRankingPage = 1; state.totalRankedItems = 0; state.currentRankingType = RANKING_TYPE.ARTISTS; dom.loadMoreArtistsBtn.style.display = 'none'; dom.loadMoreSongsBtn.style.display = 'none'; if (dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'none'; dom.rankingAnalysisArea.style.display = 'block'; dom.rankingTitle.textContent = "Top Artists (Weighted by Rank)"; dom.rankingContent.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">Loading artist ranking...</p>'; try { const data = await fetchArtistRankingData(state.filename, state.currentRankingPage, state.rankingPageSize); state.totalRankedItems = data.total_artists; renderArtistTable(data.artists, false); if (state.totalRankedItems > 0 && dom.tableExportButtonsContainer) { dom.tableExportButtonsContainer.style.display = 'flex'; } if (state.totalRankedItems > state.rankingPageSize * state.currentRankingPage) { dom.loadMoreArtistsBtn.style.display = 'inline-block'; state.currentRankingPage++; } else { dom.loadMoreArtistsBtn.style.display = 'none'; if (state.totalRankedItems > 0) showMessage('All artists loaded.', 'success', 1500); } if (state.totalRankedItems > 0) showMessage('Top artist analysis complete.', 'success'); else showMessage('No artist ranking data found.', 'info'); } catch (error) { console.error('Artist analysis error:', error); showMessage(`Artist analysis failed: ${error.message}`, 'error'); dom.rankingContent.innerHTML = `<p class="text-center text-red-500 py-4">Error loading artist ranking: ${error.message}</p>`; if (dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'none'; } finally { setLoadingState(false, dom.analyzeArtistsBtn); } }
    async function handleSongAnalysis() { /* ... (保持不变) ... */ if (state.isLoading || !state.filename) { showMessage('Please upload a file first.', 'error'); return; } setLoadingState(true, dom.analyzeSongsBtn); state.currentRankingPage = 1; state.totalRankedItems = 0; state.currentRankingType = RANKING_TYPE.SONGS; dom.loadMoreArtistsBtn.style.display = 'none'; dom.loadMoreSongsBtn.style.display = 'none'; if (dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'none'; dom.rankingAnalysisArea.style.display = 'block'; dom.rankingTitle.textContent = "Top Songs (Weighted by Rank)"; dom.rankingContent.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 py-4">Loading song ranking...</p>'; try { const data = await fetchTopSongData(state.filename, state.currentRankingPage, state.rankingPageSize); state.totalRankedItems = data.total_songs; renderSongTable(data.songs, false); if (state.totalRankedItems > 0 && dom.tableExportButtonsContainer) { dom.tableExportButtonsContainer.style.display = 'flex'; } if (state.totalRankedItems > state.rankingPageSize * state.currentRankingPage) { dom.loadMoreSongsBtn.style.display = 'inline-block'; state.currentRankingPage++; } else { dom.loadMoreSongsBtn.style.display = 'none'; if (state.totalRankedItems > 0) showMessage('All songs loaded.', 'success', 1500); } if (state.totalRankedItems > 0) showMessage('Top song analysis complete.', 'success'); else showMessage('No song ranking data found.', 'info'); } catch (error) { console.error('Song analysis error:', error); showMessage(`Song analysis failed: ${error.message}`, 'error'); dom.rankingContent.innerHTML = `<p class="text-center text-red-500 py-4">Error loading song ranking: ${error.message}</p>`; if (dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'none'; } finally { setLoadingState(false, dom.analyzeSongsBtn); } }
    async function handleLoadMoreArtists() { /* ... (保持不变) ... */ if (state.isLoading || !state.filename || state.currentRankingType !== RANKING_TYPE.ARTISTS) return; setLoadingState(true, dom.loadMoreArtistsBtn); try { const data = await fetchArtistRankingData(state.filename, state.currentRankingPage, state.rankingPageSize); renderArtistTable(data.artists, true); state.totalRankedItems = data.total_artists; if (state.totalRankedItems > state.rankingPageSize * state.currentRankingPage) { dom.loadMoreArtistsBtn.style.display = 'inline-block'; state.currentRankingPage++; } else { dom.loadMoreArtistsBtn.style.display = 'none'; showMessage('All artists loaded.', 'success', 1500); } if (state.totalRankedItems > 0 && dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'flex'; } catch (error) { console.error('Load more artists error:', error); showMessage(`Failed to load more artists: ${error.message}`, 'error'); dom.loadMoreArtistsBtn.style.display = 'none'; } finally { setLoadingState(false, dom.loadMoreArtistsBtn); } }
    async function handleLoadMoreSongs() { /* ... (保持不变) ... */ if (state.isLoading || !state.filename || state.currentRankingType !== RANKING_TYPE.SONGS) return; setLoadingState(true, dom.loadMoreSongsBtn); try { const data = await fetchTopSongData(state.filename, state.currentRankingPage, state.rankingPageSize); renderSongTable(data.songs, true); state.totalRankedItems = data.total_songs; if (state.totalRankedItems > state.rankingPageSize * state.currentRankingPage) { dom.loadMoreSongsBtn.style.display = 'inline-block'; state.currentRankingPage++; } else { dom.loadMoreSongsBtn.style.display = 'none'; showMessage('All songs loaded.', 'success', 1500); } if (state.totalRankedItems > 0 && dom.tableExportButtonsContainer) dom.tableExportButtonsContainer.style.display = 'flex'; } catch (error) { console.error('Load more songs error:', error); showMessage(`Failed to load more songs: ${error.message}`, 'error'); dom.loadMoreSongsBtn.style.display = 'none'; } finally { setLoadingState(false, dom.loadMoreSongsBtn); } }


    // --- 导出功能处理函数 ---

    /**
     * 将指定的 Chart.js 实例导出为带背景色的 PNG 文件。
     * @param {Chart|null} chartInstance - Chart.js 实例。
     * @param {string} filenamePrefix - 导出文件名的前缀。
     */
    function exportChartAsPNG(chartInstance, filenamePrefix = 'chart') {
        if (!chartInstance || !chartInstance.canvas) {
            showMessage('Chart instance or canvas not found.', 'error'); return;
        }
        try {
            const ctx = chartInstance.ctx; const canvas = chartInstance.canvas;
            ctx.save(); ctx.globalCompositeOperation = 'destination-over';
            ctx.fillStyle = state.isDarkMode ? '#1f2937' : '#ffffff'; // gray-800 or white
            ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.restore();
            const imageBase64 = chartInstance.toBase64Image('image/png', 1);
            chartInstance.update('none'); // 清理背景
            const link = document.createElement('a'); link.href = imageBase64;
            const safePrefix = filenamePrefix.replace(/[^a-z0-9_\-]/gi, '_').toLowerCase();
            link.download = `${safePrefix}_${chartInstance.config.type}_chart.png`;
            document.body.appendChild(link); link.click(); document.body.removeChild(link);
            showMessage('Chart exported as PNG.', 'success');
        } catch (error) {
            console.error("Error exporting chart:", error); showMessage(`Failed to export chart: ${error.message}`, 'error');
            if (chartInstance) { try { chartInstance.update('none'); } catch (redrawError) { console.error("Error redrawing chart after export error:", redrawError); } }
        }
    }

    /**
     * 处理表格导出按钮点击事件 (CSV 或 XLSX)。
     * @param {'csv'|'xlsx'} format - 导出的文件格式。
     */
    function handleTableExport(format) {
        if (state.isLoading) { showMessage('Please wait for the current operation to finish.', 'info'); return; }
        if (!state.filename) { showMessage('Please upload and analyze a file first.', 'error'); return; }
        if (!state.currentRankingType) { showMessage('No ranking data available to export.', 'error'); return; }

        // 使用修正后的 API 端点 (包含 /analyze 前缀)
        const exportUrl = `${API_ENDPOINTS.EXPORT_RANKING}?file=${encodeURIComponent(state.filename)}&type=${state.currentRankingType}&format=${format}`;
        console.log(`Triggering export: ${exportUrl}`);
        window.location.href = exportUrl;
        showMessage(`Exporting ${state.currentRankingType} as ${format.toUpperCase()}...`, 'info', 2000);
    }


    // --- Initialization (初始化) ---
    function resetApp() { /* ... (保持不变) ... */ state.filename = null; state.columnsInfo = []; state.selectedColumn = null; state.isLoading = false; state.currentWeightColumn = ''; state.currentRankingPage = 1; state.totalRankedItems = 0; state.currentRankingType = null; resetUIComponents(); setLoadingState(false); }

    function init() {
        console.log("Initializing application...");
        try { initCharts(); applyInitialTheme(); resetApp(); }
        catch(error) { console.error("Error during initialization steps:", error); document.body.innerHTML = `<div class="p-4 text-red-700 bg-red-100 border border-red-400 rounded">Application failed to initialize. Please check the console (F12) for errors. Error: ${error.message}</div>`; return; }

        console.log("Attaching event listeners...");
        try {
            dom.fileInput.addEventListener('change', handleFileUpload);
            dom.analyzeArtistsBtn.addEventListener('click', handleArtistAnalysis);
            dom.analyzeSongsBtn.addEventListener('click', handleSongAnalysis);
            dom.loadMoreArtistsBtn.addEventListener('click', handleLoadMoreArtists);
            dom.loadMoreSongsBtn.addEventListener('click', handleLoadMoreSongs);
            dom.weightColumnSelect.addEventListener('change', handleWeightChange);
            if (dom.darkModeToggle) { dom.darkModeToggle.addEventListener('click', toggleDarkMode); console.log("Dark mode listener attached successfully."); }
            else { console.error("Dark mode toggle button (#darkModeToggle) not found!"); }

            // 附加导出按钮的事件监听器 (添加安全检查)
            if (dom.exportBarChartBtn) { dom.exportBarChartBtn.addEventListener('click', () => exportChartAsPNG(state.barChartInstance, state.selectedColumn?.name || 'histogram')); }
            else { console.error("Export Bar Chart button not found!"); }
            if (dom.exportPieChartBtn) { dom.exportPieChartBtn.addEventListener('click', () => exportChartAsPNG(state.pieChartInstance, state.selectedColumn?.name || 'pie')); }
            else { console.error("Export Pie Chart button not found!"); }
            if (dom.exportTableCsvBtn) { dom.exportTableCsvBtn.addEventListener('click', () => handleTableExport('csv')); }
            else { console.error("Export Table CSV button not found!"); }
            if (dom.exportTableXlsxBtn) { dom.exportTableXlsxBtn.addEventListener('click', () => handleTableExport('xlsx')); }
            else { console.error("Export Table XLSX button not found!"); }

        } catch(error) { console.error("Error attaching event listeners:", error); showMessage("Error setting up interactions. Some buttons might not work.", "error", 5000); }
        console.log("Initialization complete.");
    }

    // --- Start Application (启动应用程序) ---
    init();

}); // End of DOMContentLoaded listener
