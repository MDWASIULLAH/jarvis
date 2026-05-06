(function () {
    const recognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
    const commandInput = document.getElementById('CommandInput');
    const sendBtn = document.getElementById('SendBtn');
    const micBtn = document.getElementById('MicBtn');
    const stopVoiceBtn = document.getElementById('StopVoiceBtn');
    const modelPickerBtn = document.getElementById('ModelPickerBtn');
    const modelMenu = document.getElementById('ModelMenu');
    const currentModelName = document.getElementById('CurrentModelName');
    const plusMenuBtn = document.getElementById('PlusMenuBtn');
    const plusMenu = document.getElementById('PlusMenu');
    const accountButton = document.getElementById('AccountButton');
    const accountMenu = document.getElementById('AccountMenu');
    const sidebar = document.getElementById('Sidebar');
    const brandGlyph = document.querySelector('.brand-glyph');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const mobileSidebarBtn = document.getElementById('MobileSidebarBtn');
    const topTrainBtn = document.getElementById('TopTrainBtn');
    const historyList = document.getElementById('HistoryList');
    const clearHistoryBtn = document.getElementById('ClearHistoryBtn');
    const previewModal = document.getElementById('PreviewModal');
    const previewFrame = document.getElementById('PreviewFrame');
    const closePreviewBtn = document.getElementById('ClosePreviewBtn');
    const openPreviewBtn = document.getElementById('OpenPreviewBtn');
    const consoleLog = document.getElementById('ConsoleLog');
    const liveTranscript = document.getElementById('LiveTranscript');
    const modeTitle = document.getElementById('ModeTitle');
    const backendBadge = document.getElementById('BackendBadge');
    const voiceBadge = document.getElementById('VoiceBadge');
    const connectionPanel = document.getElementById('ConnectionPanel');
    const connectionTitle = document.getElementById('ConnectionTitle');
    const connectionDetails = document.getElementById('ConnectionDetails');
    const voiceValue = document.getElementById('VoiceValue');
    const aiValue = document.getElementById('AiValue');
    const cpuValue = document.getElementById('CpuValue');
    const approvalPanel = document.getElementById('ApprovalPanel');
    const approvalMessage = document.getElementById('ApprovalMessage');
    const approvalDetails = document.getElementById('ApprovalDetails');
    const approveBtn = document.getElementById('ApproveBtn');
    const cancelBtn = document.getElementById('CancelBtn');
    const settingsView = document.getElementById('SettingsView');
    const terminalView = document.getElementById('TerminalView');
    const dashboardViews = document.querySelectorAll('.dashboard-view');
    const apiEnabled = document.getElementById('ApiEnabled');
    const apiKeyInput = document.getElementById('ApiKeyInput');
    const apiEndpointInput = document.getElementById('ApiEndpointInput');
    const apiModelInput = document.getElementById('ApiModelInput');
    const searxngUrlInput = document.getElementById('SearxngUrlInput');
    const ollamaModelInput = document.getElementById('OllamaModelInput');
    const apiStatus = document.getElementById('ApiStatus');
    const saveApiBtn = document.getElementById('SaveApiBtn');
    const clearApiBtn = document.getElementById('ClearApiBtn');
    const dailyBriefingToggle = document.getElementById('DailyBriefingToggle');
    const whatsappNumberInput = document.getElementById('WhatsappNumberInput');
    const briefingBtn = document.getElementById('BriefingBtn');
    const shareBriefingBtn = document.getElementById('ShareBriefingBtn');
    const brainTestBtn = document.getElementById('BrainTestBtn');
    const terminalInput = document.getElementById('TerminalInput');
    const terminalRunBtn = document.getElementById('TerminalRunBtn');
    const terminalOutput = document.getElementById('TerminalOutput');
    const trainModelBtn = document.getElementById('TrainModelBtn');
    const knowledgeLinkInput = document.getElementById('KnowledgeLinkInput');
    const addKnowledgeLinkBtn = document.getElementById('AddKnowledgeLinkBtn');
    const knowledgeTextInput = document.getElementById('KnowledgeTextInput');
    const addKnowledgeTextBtn = document.getElementById('AddKnowledgeTextBtn');
    const datasetInput = document.getElementById('DatasetInput');
    const importDatasetBtn = document.getElementById('ImportDatasetBtn');
    const knowledgeAskInput = document.getElementById('KnowledgeAskInput');
    const askKnowledgeBtn = document.getElementById('AskKnowledgeBtn');
    const trainingStatus = document.getElementById('TrainingStatus');
    const settingsTitle = document.getElementById('SettingsTitle');

    let recognitionInstance = null;
    let isListening = false;
    let isBusy = false;
    let finalTranscript = '';
    let pendingApproval = null;
    let bridgeAvailable = false;
    let lastHealth = null;
    let lastBriefingMessage = '';
    let currentSettings = {};
    let voiceMuted = false;
    let thinkingRow = null;
    let lastCode = '';
    let lastCodeLanguage = '';
    let lastCodePrompt = '';
    let lastGeneratedMessage = '';

    const bridgeUrl = 'http://127.0.0.1:8765';
    const restartInstruction = 'Run START_JARVIS.bat, then open http://127.0.0.1:8765/index.html.';
    const historyStorageKey = 'jarvis.chat.history.v1';
    const starterHistory = [
        { title: 'What Jarvis can do', command: 'what can you do' },
        { title: 'YouTube Shorts control', command: 'open youtube shorts and start scrolling' },
        { title: 'Daily news briefing', command: 'daily briefing' },
        { title: 'Email drafting', command: 'write email about project delay' },
    ];

    const correctionMap = {
        opne: 'open',
        oppen: 'open',
        claculator: 'calculator',
        calclator: 'calculator',
        calculater: 'calculator',
        calcuator: 'calculator',
        calculaor: 'calculator',
        calcualte: 'calculate',
        calcuate: 'calculate',
        calulate: 'calculate',
        inti: 'into',
        intoo: 'into',
        notpad: 'notepad',
        gogle: 'google',
        youtub: 'youtube',
        whatsap: 'whatsapp',
        whatapp: 'whatsapp',
        whatsaap: 'whatsapp',
        crowl: 'crawl',
        crawel: 'crawl',
        scape: 'scrape',
        scrap: 'scrape',
        emal: 'email',
        newas: 'news',
        neaws: 'news',
        bussines: 'business',
        busines: 'business',
        sprot: 'sport',
        sprots: 'sports',
        breifing: 'briefing',
        sumarize: 'summarize',
        serch: 'search',
        seach: 'search',
        writ: 'write',
        wrte: 'write',
        wrtie: 'write',
        rite: 'write',
        reed: 'read',
        red: 'read',
        shoets: 'shorts',
        shoet: 'shorts',
        shot: 'shorts',
        shots: 'shorts',
        wikipidia: 'wikipedia',
        wikipidea: 'wikipedia',
        skil: 'skill',
        skils: 'skills',
    };

    const websiteAliases = {
        google: 'https://www.google.com',
        youtube: 'https://www.youtube.com',
        github: 'https://github.com',
        gmail: 'https://mail.google.com',
        chatgpt: 'https://chatgpt.com',
        'whatsapp web': 'https://web.whatsapp.com',
    };

    const browserAppNames = new Set([
        'notepad',
        'calculator',
        'calc',
        'chrome',
        'edge',
        'microsoft edge',
        'file explorer',
        'explorer',
        'paint',
        'task manager',
        'vscode',
        'visual studio code',
        'word',
        'excel',
        'powerpoint',
        'outlook',
        'spotify',
        'whatsapp',
    ]);

    function hasBackend() {
        return typeof window.eel !== 'undefined' && typeof window.eel.process_command === 'function';
    }

    function normalize(value) {
        return (value || '').replace(/\s+/g, ' ').trim();
    }

    function correctCommand(command) {
        let corrected = normalize(command).split(' ').map((word) => {
            const prefix = word.match(/^\W*/)[0];
            const suffix = word.match(/\W*$/)[0];
            const core = word.slice(prefix.length, suffix ? -suffix.length : undefined);
            const replacement = correctionMap[core.toLowerCase()];
            return replacement ? `${prefix}${replacement}${suffix}` : word;
        }).join(' ');

        corrected = corrected.replace(/\bopen\s+calc\b/i, 'open calculator');
        corrected = corrected.replace(/\bsend\s+whatsapp\b/i, 'share to whatsapp');
        corrected = corrected.replace(/\b(today|daily)\s+news\b/i, 'daily briefing');
        corrected = corrected.replace(/^(hey|hi|hello|ok|okay)\s+jarvis[,\s:;-]*/i, '');
        corrected = corrected.replace(/^jarvis[,\s:;-]+/i, '');
        corrected = corrected.replace(/\bopen\s+(my|the)\s+/i, 'open ');
        corrected = corrected.replace(/\bopen\s+(vs code|vscode|visual code)\b/i, 'open visual studio code');
        return corrected;
    }

    function now() {
        return new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        });
    }

    function setLiveTranscript(value) {
        liveTranscript.textContent = normalize(value) || 'Awaiting input';
    }

    function resetChatSurface() {
        document.body.classList.remove('chat-started');
        consoleLog.replaceChildren();
        setMode('How can I help?');
        setLiveTranscript('Ask me to open apps, read links, write code, draft email, train memory, or run a terminal command with approval.');
    }

    function closeFloatingMenus() {
        modelMenu.classList.add('hidden');
        plusMenu.classList.add('hidden');
        accountMenu.classList.add('hidden');
        modelPickerBtn.setAttribute('aria-expanded', 'false');
        plusMenuBtn.setAttribute('aria-expanded', 'false');
        accountButton.setAttribute('aria-expanded', 'false');
    }

    function readHistory() {
        try {
            const raw = localStorage.getItem(historyStorageKey);
            if (raw === null) {
                return starterHistory;
            }
            const stored = JSON.parse(raw || '[]');
            if (Array.isArray(stored)) {
                return stored.filter((item) => item && item.title && item.command);
            }
        } catch (error) {
            localStorage.removeItem(historyStorageKey);
        }
        return starterHistory;
    }

    function titleFromCommand(command) {
        const cleaned = normalize(command)
            .replace(/^(please\s+)?(can you\s+)?/i, '')
            .replace(/^(jarvis\s+)?/i, '')
            .replace(/\s+/g, ' ')
            .trim();
        if (!cleaned) return 'New chat';
        const compact = cleaned
            .replace(/^search\s+/i, 'Search: ')
            .replace(/^write\s+/i, 'Write: ')
            .replace(/^draft\s+/i, 'Draft: ')
            .replace(/^open\s+/i, 'Open: ')
            .replace(/^tell me about\s+/i, 'About: ');
        return compact.length > 34 ? `${compact.slice(0, 31).trim()}...` : compact;
    }

    function renderHistory() {
        if (!historyList) return;
        const items = readHistory().slice(0, 28);
        historyList.replaceChildren();
        if (!items.length) {
            const empty = document.createElement('div');
            empty.className = 'history-empty';
            empty.textContent = 'Your chats will appear here.';
            historyList.appendChild(empty);
            return;
        }

        items.forEach((item) => {
            const button = document.createElement('button');
            button.className = 'recent-chat history-chat';
            button.type = 'button';
            button.textContent = item.title;
            button.title = item.command;
            button.addEventListener('click', async () => {
                commandInput.value = item.command;
                setLiveTranscript(item.command);
                await processCommand(item.command);
                commandInput.value = '';
                closeSidebarOnMobile();
            });
            historyList.appendChild(button);
        });
    }

    function rememberHistory(command) {
        const text = normalize(command);
        if (!text || /^(confirm|cancel|yes|no)\b/i.test(text)) return;

        const current = readHistory().filter((item) => item.command.toLowerCase() !== text.toLowerCase());
        const next = [{ title: titleFromCommand(text), command: text, at: Date.now() }, ...current].slice(0, 40);
        localStorage.setItem(historyStorageKey, JSON.stringify(next));
        renderHistory();
    }

    function setTopTrainingState(active) {
        if (!topTrainBtn) return;
        const label = topTrainBtn.querySelector('span');
        topTrainBtn.classList.toggle('training', active);
        topTrainBtn.disabled = active;
        if (label) {
            label.textContent = active ? 'Training' : 'Train';
        }
    }

    function toggleFloatingMenu(menu, button) {
        const willOpen = menu.classList.contains('hidden');
        closeFloatingMenus();
        if (willOpen) {
            menu.classList.remove('hidden');
            button.setAttribute('aria-expanded', 'true');
        }
    }

    function toggleSidebar() {
        document.body.classList.toggle('sidebar-collapsed');
        closeFloatingMenus();
    }

    function isMobileLayout() {
        return window.matchMedia('(max-width: 720px)').matches;
    }

    function closeSidebarOnMobile() {
        if (isMobileLayout()) {
            document.body.classList.add('sidebar-collapsed');
        }
    }

    function selectModel(modelName) {
        const nextModel = modelName || 'JS 1';
        currentModelName.textContent = nextModel;
        modelMenu.querySelectorAll('[data-model-name]').forEach((button) => {
            const active = button.dataset.modelName === nextModel;
            button.classList.toggle('selected', active);
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = active ? 'fas fa-check' : (button.dataset.modelName.includes('Code') ? 'fas fa-code' : 'fas fa-bolt');
            }
        });
        closeFloatingMenus();
        addToConsole(`${nextModel} selected.`, 'system');
        setLiveTranscript(`${nextModel} selected.`);
    }

    async function runPlusAction(action) {
        closeFloatingMenus();
        document.body.classList.add('chat-started');

        if (action === 'plan') {
            commandInput.value = 'make a plan for ';
            setMode('Plan');
            setLiveTranscript('Plan mode ready. Write your goal after "make a plan for".');
            addToConsole('Plan mode ready. Tell Jarvis the goal and it will break it into steps.', 'system');
            commandInput.focus();
            commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length);
            return;
        }

        if (action === 'media') {
            commandInput.value = 'read link ';
            setMode('Media');
            setLiveTranscript('Paste a URL after "read link" to summarize it.');
            addToConsole('Media mode ready. Paste a link and Jarvis will read or summarize it.', 'system');
            commandInput.focus();
            commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length);
            return;
        }

        if (action === 'mentions') {
            commandInput.value = '@Jarvis ';
            setMode('Mentions');
            setLiveTranscript('Jarvis mention inserted.');
            addToConsole('Mention ready. Type your request after @Jarvis.', 'system');
            commandInput.focus();
            commandInput.setSelectionRange(commandInput.value.length, commandInput.value.length);
            return;
        }

        if (action === 'workflows') {
            setMode('Workflows');
            addToConsole('Workflow started: daily briefing.', 'system');
            await processCommand('daily briefing');
        }
    }

    function extractFirstCodeBlock(message) {
        const match = String(message || '').match(/```([a-zA-Z0-9+#-]*)\n([\s\S]*?)```/);
        if (!match) {
            return null;
        }
        return {
            language: match[1] || 'code',
            code: match[2].replace(/^\n+|\n+$/g, ''),
        };
    }

    function rememberGeneratedCode(message, prompt) {
        const block = extractFirstCodeBlock(message);
        if (!block) {
            return;
        }
        lastCode = block.code;
        lastCodeLanguage = block.language.toLowerCase();
        lastCodePrompt = prompt || lastCodePrompt || 'generated code';
        lastGeneratedMessage = message;
    }

    function canPreviewCode(language = lastCodeLanguage, code = lastCode) {
        const lang = String(language || '').toLowerCase();
        return Boolean(code) && ['html', 'web', 'website'].includes(lang);
    }

    function openPreview(code = lastCode, language = lastCodeLanguage) {
        if (!canPreviewCode(language, code)) {
            addToConsole('Preview is available for complete HTML website code. Ask me to convert this to HTML if you want a live preview.', 'system');
            return;
        }
        lastCode = code;
        lastCodeLanguage = String(language || 'html').toLowerCase();
        previewFrame.srcdoc = code;
        previewModal.classList.remove('hidden');
    }

    function closePreview() {
        previewModal.classList.add('hidden');
    }

    function openPreviewInNewPage() {
        if (!lastCode) return;
        const blob = new Blob([lastCode], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        window.setTimeout(() => URL.revokeObjectURL(url), 30000);
    }

    function showSettingsTab(tabName = 'General') {
        const selected = tabName || 'General';
        document.querySelectorAll('[data-settings-tab]').forEach((button) => {
            button.classList.toggle('active', button.dataset.settingsTab === selected);
        });
        document.querySelectorAll('[data-settings-panel]').forEach((panel) => {
            panel.classList.toggle('hidden', panel.dataset.settingsPanel !== selected);
        });
        settingsTitle.textContent = selected === 'DataControls' ? 'Data controls' : selected;
    }

    function setMode(title) {
        modeTitle.textContent = title;
    }

    function setBusy(value) {
        isBusy = value;
        sendBtn.disabled = value;
        commandInput.disabled = value;
        setMode(value ? 'Working' : 'Ready');
    }

    function cleanAssistantText(message) {
        const codeBlocks = [];
        let source = String(message || '').replace(/\r\n/g, '\n');
        source = source.replace(/<!--[\s\S]*?-->/g, ' ');
        source = source.replace(/```[\s\S]*?```/g, (block) => {
            codeBlocks.push(block);
            return `@@JARVIS_CODE_BLOCK_${codeBlocks.length - 1}@@`;
        });

        const lines = source.split('\n');
        const cleaned = lines.filter((line) => {
            let text = line.trim();
            const lowered = text.toLowerCase();
            if (['markdownlint-disable', 'shields.io', 'badge.svg', '<img', '<picture', '<div', '</div', '<br', 'align="center"'].some((marker) => lowered.includes(marker))) return false;
            if (/^Router:/i.test(text)) return false;
            if (/^(RAG context used|Skill context used|Scraper engine):/i.test(text)) return false;
            if (/^[*_=-]{3,}$/.test(text)) return false;
            return true;
        }).map((line) => {
            let text = line.trim();
            text = text.replace(/^\s{0,3}#{1,6}\s*/g, '');
            text = text.replace(/^\s*>\s*/g, '');
            text = text.replace(/\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/ig, '$1: ');
            text = text.replace(/!\[[^\]]*\]\([^)]+\)/g, '');
            text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '$1 - $2');
            text = text.replace(/<[^>]+>/g, ' ');
            text = text.replace(/^GitHub README:\s*/i, '');
            text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
            text = text.replace(/__([^_]+)__/g, '$1');
            text = text.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '$1');
            text = text.replace(/`{1,2}([^`\n]+)`{1,2}/g, '$1');
            text = text.replace(/\s+/g, ' ').trim();
            return text;
        }).join('\n');

        let output = cleaned.replace(/\n{3,}/g, '\n\n').trim();
        codeBlocks.forEach((block, index) => {
            output = output.replace(`@@JARVIS_CODE_BLOCK_${index}@@`, block);
        });
        return output;
    }

    function isIdentityQuestion(command) {
        const normalized = normalize(command).toLowerCase().replace(/what's/g, 'whats');
        return /^(whats|what is|tell me)\s+(your|you)\s+name\??$/.test(normalized)
            || /^(who are you|what are you|introduce yourself)\??$/.test(normalized)
            || /^(your name|name)\??$/.test(normalized);
    }

    function jarvisIdentityAnswer() {
        return [
            'My name is Jarvis.',
            '',
            'I am your local desktop AI assistant. I can answer questions, search with the free local stack, write code, read links, open apps, and draft messages or emails after asking permission.',
        ].join('\n');
    }

    function normalizeSourceUrl(value) {
        const url = String(value || '').trim().replace(/[),.;]+$/g, '');
        if (!url) return '';
        return /^https?:\/\//i.test(url) ? url : `https://${url}`;
    }

    function sourceHost(url) {
        try {
            return new URL(normalizeSourceUrl(url)).hostname.replace(/^www\./, '');
        } catch (error) {
            return '';
        }
    }

    function makeInlineLink(url, label = 'Open link') {
        const anchor = document.createElement('a');
        anchor.className = 'inline-source-link';
        anchor.href = normalizeSourceUrl(url);
        anchor.target = '_blank';
        anchor.rel = 'noopener noreferrer';
        anchor.title = 'Open original source';
        const icon = document.createElement('i');
        icon.className = 'fas fa-arrow-up-right-from-square';
        const text = document.createElement('span');
        text.textContent = label;
        anchor.append(icon, text);
        return anchor;
    }

    function appendInlineText(parent, value) {
        const text = String(value || '');
        const pattern = /(https?:\/\/[^\s)]+|www\.[^\s)]+)/ig;
        let cursor = 0;
        let match;
        while ((match = pattern.exec(text)) !== null) {
            if (match.index > cursor) {
                parent.appendChild(document.createTextNode(text.slice(cursor, match.index)));
            }
            parent.appendChild(makeInlineLink(match[0], sourceHost(match[0]) || 'Open link'));
            cursor = pattern.lastIndex;
        }
        if (cursor < text.length) {
            parent.appendChild(document.createTextNode(text.slice(cursor)));
        }
    }

    function parseSourceItems(value) {
        const body = String(value || '')
            .replace(/^Sources?:\s*/i, '')
            .trim();
        if (!body) return [];

        const items = [];
        const hasNumberedSources = /(^|\n)\s*\d+\.\s+/.test(body);
        const chunks = body.includes(';') && !hasNumberedSources
            ? body.split(/\s*;\s*/)
            : (hasNumberedSources ? body.split(/(?=(?:^|\n)\s*\d+\.\s+)/) : body.split('\n'));

        chunks.forEach((line) => {
            const text = line.trim();
            if (!text) return;
            if (!/(https?:\/\/[^\s)]+|www\.[^\s)]+)/i.test(text) && hasNumberedSources && !/^\d+\.\s+/.test(text)) {
                return;
            }
            const urlMatch = text.match(/(https?:\/\/[^\s)]+|www\.[^\s)]+)/i);
            const url = urlMatch ? normalizeSourceUrl(urlMatch[0]) : '';
            const title = text
                .replace(/^\d+\.\s*/, '')
                .replace(/\s+-\s+(https?:\/\/[^\s)]+|www\.[^\s)]+)/i, '')
                .replace(/(https?:\/\/[^\s)]+|www\.[^\s)]+)/i, '')
                .trim();

            if (url || title) {
                items.push({
                    title: title || sourceHost(url) || 'Source',
                    url,
                    host: sourceHost(url),
                });
            }
        });

        return items;
    }

    function appendSources(container, sourceText) {
        const items = parseSourceItems(sourceText);
        if (!items.length) return;

        const block = document.createElement('div');
        block.className = 'source-list';
        const title = document.createElement('div');
        title.className = 'source-list-title';
        title.textContent = 'Sources';
        block.appendChild(title);

        items.slice(0, 6).forEach((item) => {
            const row = item.url ? document.createElement('a') : document.createElement('div');
            row.className = 'source-item';
            if (item.url) {
                row.href = item.url;
                row.target = '_blank';
                row.rel = 'noopener noreferrer';
                row.title = 'Open original source';
            }
            const icon = document.createElement('span');
            icon.className = 'source-icon';
            icon.innerHTML = '<i class="fas fa-arrow-up-right-from-square"></i>';
            const label = document.createElement('span');
            label.className = 'source-label';
            const strong = document.createElement('strong');
            strong.textContent = item.title;
            const small = document.createElement('small');
            small.textContent = item.host || 'local memory';
            label.append(strong, small);
            row.append(icon, label);
            block.appendChild(row);
        });
        container.appendChild(block);
    }

    function appendFormattedText(container, value) {
        const text = cleanAssistantText(value);
        if (!text) return;

        const sourceSplit = text.match(/(^|\n)\s*Sources?:\s*/i);
        if (sourceSplit) {
            const before = text.slice(0, sourceSplit.index);
            const sources = text.slice(sourceSplit.index).trim();
            appendFormattedText(container, before);
            appendSources(container, sources);
            return;
        }

        const singleSource = text.match(/\n?\s*Source:\s+(https?:\/\/[^\s)]+|www\.[^\s)]+)\s*$/i);
        const mainText = singleSource ? text.slice(0, singleSource.index).trim() : text;

        const blocks = mainText.split(/\n{2,}/).map((block) => block.trim()).filter(Boolean);
        if (blocks.length > 4) {
            blocks.slice(0, 3).forEach((block) => appendFormattedText(container, block));
            const disclosure = document.createElement('details');
            disclosure.className = 'technical-details';
            const summaryNode = document.createElement('summary');
            summaryNode.textContent = 'Technical details';
            const detailBody = document.createElement('div');
            appendFormattedText(detailBody, blocks.slice(3).join('\n\n'));
            disclosure.append(summaryNode, detailBody);
            container.appendChild(disclosure);
        } else {
            blocks.forEach((blockText) => {
            const block = blockText.trim();
            if (!block) return;
            const lines = block.split('\n').map((line) => line.trim()).filter(Boolean);
            const noteMatch = block.match(/^(NOTE|TIP|IMPORTANT|WARNING|CAUTION|ERROR):\s*(.+)$/i);
            if (noteMatch) {
                const note = document.createElement('div');
                note.className = `answer-callout ${noteMatch[1].toLowerCase()}`;
                const label = document.createElement('strong');
                label.textContent = noteMatch[1].toUpperCase();
                const body = document.createElement('span');
                appendInlineText(body, noteMatch[2]);
                note.append(label, body);
                container.appendChild(note);
                return;
            }

            if (lines.length && lines.every((line) => /^[-*]\s+/.test(line))) {
                const list = document.createElement('ul');
                list.className = 'answer-list';
                lines.forEach((line) => {
                    const item = document.createElement('li');
                    appendInlineText(item, line.replace(/^[-*]\s+/, ''));
                    list.appendChild(item);
                });
                container.appendChild(list);
                return;
            }

            if (lines.length === 1 && /:$/.test(lines[0]) && lines[0].length < 80) {
                const heading = document.createElement('p');
                heading.className = 'answer-section-title';
                heading.textContent = lines[0].replace(/:$/, '');
                container.appendChild(heading);
                return;
            }

            if (lines.length > 4) {
                const summary = lines.slice(0, 3).join(' ');
                const details = lines.slice(3).join('\n');
                const paragraph = document.createElement('p');
                appendInlineText(paragraph, summary);
                container.appendChild(paragraph);

                const disclosure = document.createElement('details');
                disclosure.className = 'technical-details';
                const summaryNode = document.createElement('summary');
                summaryNode.textContent = 'Technical details';
                const detailBody = document.createElement('div');
                appendFormattedText(detailBody, details);
                disclosure.append(summaryNode, detailBody);
                container.appendChild(disclosure);
                return;
            }

            const paragraph = document.createElement('p');
            appendInlineText(paragraph, lines.join(' '));
            container.appendChild(paragraph);
            });
        }

        if (singleSource) {
            appendSources(container, `Source: ${singleSource[1]}`);
        }
    }

    function renderMessageContent(container, message) {
        const source = String(message || '');
        const pattern = /```([a-zA-Z0-9+#-]*)\n([\s\S]*?)```/g;
        let cursor = 0;
        let match;

        while ((match = pattern.exec(source)) !== null) {
            appendFormattedText(container, source.slice(cursor, match.index));

            const language = match[1] || 'code';
            const code = match[2].replace(/^\n+|\n+$/g, '');
            const card = document.createElement('div');
            card.className = 'code-card';

            const header = document.createElement('div');
            header.className = 'code-card-head';
            const label = document.createElement('span');
            label.textContent = language;
            const copy = document.createElement('button');
            copy.type = 'button';
            copy.textContent = 'Copy';
            copy.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText(code);
                    copy.textContent = 'Copied';
                    window.setTimeout(() => {
                        copy.textContent = 'Copy';
                    }, 1200);
                } catch (error) {
                    copy.textContent = 'Copy failed';
                }
            });
            const preview = document.createElement('button');
            preview.type = 'button';
            preview.className = 'preview-code-btn';
            preview.textContent = 'Preview';
            preview.hidden = !canPreviewCode(language, code);
            preview.addEventListener('click', () => openPreview(code, language));

            const rewrite = document.createElement('button');
            rewrite.type = 'button';
            rewrite.className = 'rewrite-code-btn';
            rewrite.textContent = 'Rewrite';
            rewrite.addEventListener('click', async () => {
                await processCommand('rewrite this code better');
            });

            const pre = document.createElement('pre');
            const codeElement = document.createElement('code');
            codeElement.textContent = code;
            pre.appendChild(codeElement);
            header.append(label, preview, rewrite, copy);
            card.append(header, pre);
            container.appendChild(card);
            cursor = pattern.lastIndex;
        }

        appendFormattedText(container, source.slice(cursor));
        if (!container.childNodes.length) {
            container.textContent = cleanAssistantText(source);
        }
    }

    function addToConsole(message, tone = 'jarvis') {
        const row = document.createElement('div');
        row.className = `log-line ${tone}`;

        const time = document.createElement('span');
        time.className = 'log-time';
        time.textContent = now();

        const text = document.createElement('div');
        text.className = 'log-text';
        renderMessageContent(text, message);

        row.append(time, text);
        consoleLog.appendChild(row);
        consoleLog.scrollTop = consoleLog.scrollHeight;
        return row;
    }

    function showThinking() {
        removeThinking();
        thinkingRow = addToConsole('Thinking', 'system thinking');
    }

    function removeThinking() {
        if (thinkingRow) {
            thinkingRow.remove();
            thinkingRow = null;
        }
    }

    function speakText(text) {
        if (voiceMuted || !text || !('speechSynthesis' in window)) {
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.08;
        utterance.pitch = 0.92;
        utterance.volume = 1;
        window.speechSynthesis.speak(utterance);
    }

    function stopVoice() {
        voiceMuted = true;
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
        }
        voiceBadge.textContent = 'Voice Muted';
        voiceBadge.classList.add('warn');
        voiceValue.textContent = 'MUTED';
        addToConsole('Voice stopped.', 'system');
    }

    function tryParseJson(value) {
        if (typeof value !== 'string') {
            return value;
        }

        try {
            return JSON.parse(value);
        } catch (error) {
            return value;
        }
    }

    function shouldAnswerCodeLocally(command) {
        const normalized = command.toLowerCase();
        const asksForCode = /(write|create|generate|make)\b/.test(normalized) && /\b(code|program|website|site|page|app)\b/.test(normalized);
        const isWebWork = /\b(website|web site|webpage|web page|site|frontend|landing page|name fixer)\b/.test(normalized);
        const asksKnownLocalLanguage = /\b(html|css|javascript|react|next|nextjs|next\.js|python|java|c\+\+|cpp|c#|csharp|php|sql)\b/.test(normalized);
        return asksForCode && (isWebWork || asksKnownLocalLanguage);
    }

    function isNewsCommand(command) {
        const normalized = command.toLowerCase();
        return /\b(news|briefing)\b/.test(normalized)
            || /\b(latest|today|current)\b.*\b(ai|business|sports|sport|technology|tech|india|world|science|health|education)\b/.test(normalized);
    }

    function isSearchOrRetrievalCommand(command) {
        const normalized = command.toLowerCase();
        return /\b(search|google|news|briefing|latest|today|current|read|summarize|summary|link|crawl|scrape|extract|about|what|who|where|why|how)\b/.test(normalized)
            || /https?:\/\//i.test(command);
    }

    function localCoreOfflineMessage(command) {
        const isNews = isNewsCommand(command);
        return {
            type: isNews ? 'briefing' : 'response',
            message: [
                'Local Core is not running on port 8765, so Jarvis cannot use DDGS/SearXNG search, RAG memory, desktop control, or local scraping from this page.',
                `Backend URL: ${bridgeUrl}`,
                `Current page mode: ${location.protocol === 'file:' ? 'file browser safe mode' : `${location.host} browser safe mode`}`,
                restartInstruction,
                'I did not open Google News or browser search automatically. Start Local Core for full free local search.',
            ].join('\n'),
            briefing: isNews ? { message: 'Local Core offline. Free local search requires the backend.', sections: [] } : undefined,
        };
    }

    function localCodeWithRouter(command) {
        return localCodeFromPrompt(command);
    }

    function browserSkillContext(command) {
        const normalized = command.toLowerCase();
        const skills = [];
        if (/\b(html|css|javascript|website|webpage|react|next|frontend|preview)\b/.test(normalized)) {
            skills.push('Frontend Builder');
        }
        if (/\b(python|tkinter|script|automation)\b/.test(normalized)) {
            skills.push('Python Builder');
        }
        if (/\b(code|program|java|cpp|c\+\+|c#|php|sql|typescript)\b/.test(normalized)) {
            skills.push('Coding Architect');
        }
        if (/\b(email|message|whatsapp|draft|reply|send|share)\b/.test(normalized)) {
            skills.push('Message And Email Writer', 'Security Guard');
        }
        if (/\b(news|briefing|business|sports|ai|technology)\b/.test(normalized)) {
            skills.push('News Briefing');
        }
        if (/\b(what|who|where|why|how|explain|about|answer)\b/.test(normalized)) {
            skills.push('Answer Router');
        }
        return [...new Set(skills)].join(' + ') || 'default local skills';
    }

    function cleanGeneralTopic(topic) {
        return normalize(topic)
            .replace(/\b(for me|to me|please|in short|briefly|in detail|full details|give answer|answer me)\b/ig, ' ')
            .replace(/[?!.,:;"']+$/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function extractGeneralTopic(command) {
        const text = normalize(command);
        if (!text) {
            return '';
        }

        if (/^(help|what can you do|what can jarvis do)\b/i.test(text)) {
            return '';
        }

        const patterns = [
            /^(?:please\s+)?(?:tell|teach|explain)\s+(?:me\s+)?(?:about\s+)?(.+)$/i,
            /^(?:please\s+)?(?:what|who|where)\s+(?:is|are|was|were)\s+(.+)$/i,
            /^(?:please\s+)?(?:give|show)\s+(?:me\s+)?(?:information|details|info)\s+(?:about|on|of)\s+(.+)$/i,
            /^(?:please\s+)?(?:information|details|info)\s+(?:about|on|of)\s+(.+)$/i,
            /^(?:please\s+)?(?:about|define|describe)\s+(.+)$/i,
        ];

        for (const pattern of patterns) {
            const match = text.match(pattern);
            if (match) {
                return cleanGeneralTopic(match[1]);
            }
        }

        const normalized = text.toLowerCase();
        const looksLikeCommand = /\b(open|launch|start|run|search|google|write|draft|save|note|email|send|share|play|scroll|terminal|train|learn|news|briefing|shutdown|calculate|calculator|read file|write file)\b/.test(normalized);
        if (!looksLikeCommand && text.split(/\s+/).length <= 8) {
            return cleanGeneralTopic(text);
        }

        return '';
    }

    function isGeneralQuestion(command) {
        return Boolean(extractGeneralTopic(command));
    }

    async function fetchWikipediaSummary(topic) {
        async function readSummary(title) {
            const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title.replace(/\s+/g, '_'))}`;
            const response = await fetchWithTimeout(url, { cache: 'no-store' }, 4000);
            if (!response.ok) {
                return null;
            }
            const data = await response.json();
            if (!data.extract) {
                return null;
            }
            return {
                title: data.title || topic,
                extract: data.extract,
                url: data.content_urls?.desktop?.page || `https://en.wikipedia.org/wiki/${encodeURIComponent(title.replace(/\s+/g, '_'))}`,
            };
        }

        const direct = await readSummary(topic);
        if (direct) {
            return direct;
        }

        const searchUrl = `https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=${encodeURIComponent(topic)}&srlimit=1&format=json&origin=*`;
        const response = await fetchWithTimeout(searchUrl, { cache: 'no-store' }, 4000);
        if (!response.ok) {
            return null;
        }
        const data = await response.json();
        const title = data.query?.search?.[0]?.title;
        return title ? readSummary(title) : null;
    }

    async function browserGeneralAnswer(command) {
        const topic = extractGeneralTopic(command);
        if (!topic) {
            return null;
        }

        try {
            const summary = await fetchWikipediaSummary(topic);
            if (summary?.extract) {
                return {
                    type: 'answer',
                    message: [
                        `${summary.title}:`,
                        summary.extract,
                        '',
                        `Source: ${summary.url}`,
                    ].join('\n'),
                };
            }
        } catch (error) {
            // Network or CORS can fail in file mode; the backend gives the stronger retrieval path.
        }

        return {
            type: 'answer',
            message: [
                `I could not fetch a direct summary for ${topic} in browser-only mode.`,
                'Start Jarvis from START_JARVIS.bat for stronger local retrieval and RAG memory.',
            ].join('\n'),
        };
    }

    function contextualCommand(command) {
        const normalized = command.toLowerCase();
        if (/^(continue|go on|keep going|next)$/i.test(normalized)) {
            if (lastCode) {
                if (canPreviewCode()) {
                    openPreview();
                    return {
                        type: 'response',
                        message: 'The last code is complete, so I opened the preview. You can also say “rewrite it better”, “convert to React”, or “make it dark mode”.',
                    };
                }
                return {
                    type: 'response',
                    message: 'The last code is complete. You can say “rewrite it better”, “explain it”, or “convert it to another language”.',
                };
            }
        }

        if (/\b(preview|show preview|run preview|see website)\b/.test(normalized)) {
            openPreview();
            return {
                type: 'response',
                message: canPreviewCode() ? 'Preview opened.' : 'Preview needs a complete HTML code block first.',
            };
        }

        if (/\b(rewrite|redo|not like|don't like|do not like|make better|improve|better design|different)\b/.test(normalized) && lastCodePrompt) {
            return {
                type: 'code',
                message: localCodeFromPrompt(`${lastCodePrompt} improved polished responsive version`),
            };
        }

        if (/\b(convert|change)\b.*\b(react|next|nextjs|next\.js|html|python|javascript)\b/.test(normalized) && lastCodePrompt) {
            return {
                type: 'code',
                message: localCodeFromPrompt(`${command} for ${lastCodePrompt}`),
            };
        }

        return null;
    }

    async function callAssistant(command) {
        const correctedCommand = correctCommand(command);
        const contextual = contextualCommand(correctedCommand);
        if (contextual) {
            return contextual;
        }

        const calculation = localCalculation(correctedCommand);
        if (calculation) {
            if (/calculator/i.test(correctedCommand) || /^(open|launch|start)\b/i.test(correctedCommand)) {
                try {
                    if (hasBackend()) {
                        await window.eel.process_command('open calculator')();
                    } else {
                        await callBridge('open calculator');
                    }
                    bridgeAvailable = true;
                    applyConnectionLabels('Local Core', true);
                    return {
                        type: 'calculation',
                        message: calculation.replace('Local core can open Calculator. ', 'Opening calculator. '),
                    };
                } catch (error) {
                    return {
                        type: 'calculation',
                        message: calculation,
                    };
                }
            }
            return {
                type: 'calculation',
                message: calculation,
            };
        }

        if (hasBackend()) {
            return window.eel.process_command(correctedCommand)();
        }

        try {
            const response = await callBridge(correctedCommand);
            bridgeAvailable = true;
            applyConnectionLabels('Local Core', true);
            return response;
        } catch (error) {
            bridgeAvailable = false;
        }

        const cloudResponse = await callCloudAgent(correctedCommand);
        if (cloudResponse) {
            return cloudResponse;
        }

        if (isSearchOrRetrievalCommand(correctedCommand)) {
            applyConnectionLabels('Safe Mode', false);
            return localCoreOfflineMessage(correctedCommand);
        }

        if (isNewsCommand(correctedCommand)) {
            return browserDailyBriefing(correctedCommand);
        }

        if (shouldAnswerCodeLocally(correctedCommand)) {
            return {
                type: 'code',
                message: localCodeWithRouter(correctedCommand),
            };
        }

        if (isGeneralQuestion(correctedCommand)) {
            return browserGeneralAnswer(correctedCommand);
        }

        return fallbackProcessCommand(correctedCommand);
    }

    async function callCloudAgent(command) {
        if (location.protocol === 'file:' || location.hostname === '127.0.0.1' || location.hostname === 'localhost') {
            return null;
        }
        try {
            const response = await fetch('/api/agent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command }),
            });
            if (!response.ok) return null;
            return response.json();
        } catch (error) {
            return null;
        }
    }

    function bridgeTimeoutFor(command) {
        const normalized = command.toLowerCase();
        if (/\b(search|news|briefing|latest|today|current|read|summarize|summary|link|crawl|scrape|extract|website|about|what|who|where|why|how|train|dataset|github|kaggle)\b/.test(normalized) || /https?:\/\//i.test(command)) {
            return 24000;
        }
        return 5000;
    }

    async function callBridge(command) {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), bridgeTimeoutFor(command));

        try {
            const response = await fetch(`${bridgeUrl}/command`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Jarvis-Client': 'command-center',
                },
                body: JSON.stringify({ command }),
                signal: controller.signal,
            });

            if (!response.ok) {
                throw new Error('Bridge rejected command');
            }

            return response.json();
        } finally {
            window.clearTimeout(timeout);
        }
    }

    async function fetchWithTimeout(url, options = {}, timeoutMs = 3500) {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

        try {
            return await fetch(url, {
                ...options,
                signal: controller.signal,
            });
        } finally {
            window.clearTimeout(timeout);
        }
    }

    async function browserDailyBriefing(command = '') {
        const message = [
            'Local Core is not running on port 8765, so DDGS/SearXNG briefing is unavailable in this browser tab.',
            `Backend URL: ${bridgeUrl}`,
            restartInstruction,
            'No Google News fallback was opened automatically. Start Local Core for the free local search stack.',
        ].join('\n');
        return { type: 'briefing', message, briefing: { message, sections: [] } };
    }

    async function checkBridge() {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 800);

        try {
            const response = await fetch(`${bridgeUrl}/health`, {
                headers: { 'X-Jarvis-Client': 'command-center' },
                signal: controller.signal,
            });
            lastHealth = response.ok ? await response.json().catch(() => null) : null;
            bridgeAvailable = response.ok;
            return bridgeAvailable;
        } catch (error) {
            lastHealth = null;
            bridgeAvailable = false;
            return false;
        } finally {
            window.clearTimeout(timeout);
        }
    }

    async function canServeVoicePage() {
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 900);

        try {
            const response = await fetch(`${bridgeUrl}/index.html`, {
                signal: controller.signal,
                cache: 'no-store',
            });
            const page = await response.text();
            return response.ok && page.includes('Jarvis');
        } catch (error) {
            return false;
        } finally {
            window.clearTimeout(timeout);
        }
    }

    async function loadSettings() {
        if (!bridgeAvailable && !await checkBridge()) {
            const localSettings = JSON.parse(localStorage.getItem('jarvis-settings') || '{}');
            applySettingsToForm(localSettings);
            return;
        }

        try {
            const response = await fetch(`${bridgeUrl}/settings`, {
                headers: { 'X-Jarvis-Client': 'command-center' },
            });
            const data = await response.json();
            applySettingsToForm(data.settings || {});
        } catch (error) {
            apiStatus.textContent = 'Settings are local to this browser.';
        }
    }

    async function saveSettings(updates) {
        if (!bridgeAvailable && !await checkBridge()) {
            const current = JSON.parse(localStorage.getItem('jarvis-settings') || '{}');
            const merged = { ...current, ...updates, security_level: 'HIGH' };
            localStorage.setItem('jarvis-settings', JSON.stringify(merged));
            applySettingsToForm(merged);
            return merged;
        }

        const response = await fetch(`${bridgeUrl}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Jarvis-Client': 'command-center',
            },
            body: JSON.stringify({ settings: updates }),
        });
        const data = await response.json();
        applySettingsToForm(data.settings || {});
        return data.settings || {};
    }

    function applySettingsToForm(settings) {
        apiEnabled.checked = Boolean(settings.api_enabled);
        apiEndpointInput.value = settings.api_endpoint || 'https://api.openai.com/v1/chat/completions';
        apiModelInput.value = settings.api_model || 'gpt-4o-mini';
        if (searxngUrlInput) {
            searxngUrlInput.value = settings.searxng_url || '';
        }
        ollamaModelInput.value = settings.ollama_model || 'gemma3';
        whatsappNumberInput.value = settings.whatsapp_number || '';
        dailyBriefingToggle.checked = settings.daily_briefing !== false;
        apiKeyInput.value = '';
        currentSettings = settings;
        voiceMuted = settings.voice_enabled === false;
        document.querySelectorAll('[data-mode]').forEach((button) => {
            button.classList.toggle('active', button.dataset.mode === (settings.work_mode || 'simple'));
        });
        if (voiceMuted) {
            voiceBadge.textContent = 'Voice Muted';
            voiceBadge.classList.add('warn');
            voiceValue.textContent = 'MUTED';
        }

        if (settings.api_enabled && settings.api_key_saved && settings.searxng_url) {
            apiStatus.textContent = 'Custom API and SearXNG search enabled. Search uses no API key.';
        } else if (settings.searxng_url) {
            apiStatus.textContent = 'SearXNG search enabled. DDGS remains the default fallback.';
        } else if (settings.api_enabled && settings.api_key_saved) {
            apiStatus.textContent = 'Custom API enabled. Key saved locally.';
        } else if (settings.api_enabled) {
            apiStatus.textContent = 'Custom API enabled. Add a key to use it.';
        } else {
            apiStatus.textContent = 'Default local model active. Search uses DDGS with local fallbacks.';
        }
    }

    function parseEmailRequest(command) {
        const recipientMatch = command.match(/(?:send|compose|write|draft)\s+(?:an\s+)?email\s+(?:to|for)\s+(.+?)(?:\s+(?:subject|body|message|saying|say|about|regarding|for)\b|$)/i);
        const subjectMatch = command.match(/subject\s+(.+?)(?:\s+(?:body|message|saying|say|about|regarding|for)\b|$)/i);
        const bodyMatch = command.match(/(?:body|message|say|saying)\s+(.+)$/i);
        const aboutMatch = command.match(/(?:about|regarding|for)\s+(.+)$/i);
        const topic = (bodyMatch ? bodyMatch[1] : (aboutMatch ? aboutMatch[1] : (subjectMatch ? subjectMatch[1] : command))).trim();

        return {
            to: recipientMatch ? recipientMatch[1].trim().replace(/[,. ;]+$/, '') : '',
            subject: subjectMatch ? subjectMatch[1].trim() : emailSubjectFromTopic(topic),
            body: bodyMatch ? draftEmailBody(topic) : (aboutMatch ? draftEmailBody(topic) : ''),
        };
    }

    function emailSubjectFromTopic(topic) {
        const value = normalize(topic).toLowerCase();
        if (/(support|problem|issue|bug|not working|broken|error)/.test(value)) return 'Jarvis Support Request';
        if (/leave/.test(value)) return 'Leave Request';
        if (/(project|delay|late)/.test(value)) return 'Project Update';
        if (/(meeting|schedule)/.test(value)) return 'Meeting Request';
        if (/(job|inquiry|application)/.test(value)) return 'Professional Inquiry';
        const words = normalize(topic).replace(/^(about|regarding|for)\s+/i, '').split(/\s+/).filter(Boolean).slice(0, 7);
        if (!words.length) return 'Message Request';
        return words.map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
    }

    function draftEmailBody(topic) {
        const cleanTopic = normalize(topic).replace(/^(about|regarding|for)\s+/i, '') || 'the matter we discussed';
        return [
            'Hello,',
            '',
            `I am writing regarding ${cleanTopic}. Please review this request and let me know if any more details are needed.`,
            '',
            'Thank you.',
            '',
            'Best regards',
        ].join('\n');
    }

    function spokenMathToExpression(value) {
        let expression = normalize(value).toLowerCase();
        [
            [/\bmultiplied\s+by\b/g, '*'],
            [/\bmultiply\s+by\b/g, '*'],
            [/\bmultiply\b/g, '*'],
            [/\btimes\b/g, '*'],
            [/\binto\b/g, '*'],
            [/\bx\b/g, '*'],
            [/\bplus\b/g, '+'],
            [/\badd\b/g, '+'],
            [/\bminus\b/g, '-'],
            [/\bsubtract\b/g, '-'],
            [/\bdivided\s+by\b/g, '/'],
            [/\bdivide\s+by\b/g, '/'],
            [/\bdivide\b/g, '/'],
            [/\bover\b/g, '/'],
        ].forEach(([pattern, replacement]) => {
            expression = expression.replace(pattern, ` ${replacement} `);
        });
        return normalize(expression.replace(/×/g, '*').replace(/÷/g, '/').replace(/[^0-9+\-*/().% ]/g, ' '));
    }

    function evaluateBasicMath(expression) {
        if (!/^[0-9+\-*/().% ]+$/.test(expression) || !/[+\-*/%]/.test(expression)) {
            return null;
        }
        try {
            const value = Function(`"use strict"; return (${expression});`)();
            if (!Number.isFinite(value)) {
                return null;
            }
            return Number.isInteger(value) ? String(value) : value.toPrecision(10).replace(/\.?0+$/, '');
        } catch (error) {
            return null;
        }
    }

    function localCalculation(command) {
        const normalized = command.toLowerCase();
        if (!/\d/.test(normalized) || !/(calculate|compute|solve|what is|how much|plus|minus|multiply|times|into|divided|divide|\sx\s)/.test(normalized)) {
            return null;
        }
        let tail = command;
        const keywordMatch = command.match(/\b(calculate|compute|solve|what\s+is|how\s+much\s+is)\b(.+)$/i);
        if (keywordMatch) {
            tail = keywordMatch[2];
        } else if (normalized.includes('calculator')) {
            tail = command.replace(/^.*?\bcalculator\b/i, '');
        }
        tail = tail.replace(/\b(and\s+then|then|please|for\s+me|answer|answe|open|calculator)\b/ig, ' ');
        const expression = spokenMathToExpression(tail);
        const result = evaluateBasicMath(expression);
        if (result === null) {
            return null;
        }
        const displayExpression = expression.replace(/\*/g, '×').replace(/\//g, '÷');
        const opened = normalized.includes('calculator') || /^(open|launch|start)\b/i.test(command)
            ? 'Local core can open Calculator. '
            : '';
        return `${opened}${displayExpression} = ${result}.`;
    }

    function fallbackProcessCommand(command) {
        const text = normalize(command);
        const normalized = text.toLowerCase();

        if (!text) {
            return { type: 'response', message: 'Please say a command.' };
        }

        if (/^(hello|hi|hey)(\s+jarvis)?$/.test(normalized) || normalized === 'jarvis') {
            return { type: 'response', message: 'Hello. Jarvis is online and ready.' };
        }

        if (isIdentityQuestion(text)) {
            return { type: 'answer', message: jarvisIdentityAnswer() };
        }

        if (/\btime\b/.test(normalized)) {
            return {
                type: 'response',
                message: `The current time is ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}.`,
            };
        }

        if (/\b(date|day)\b/.test(normalized)) {
            return {
                type: 'response',
                message: `Today is ${new Date().toLocaleDateString([], { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}.`,
            };
        }

        const calculation = localCalculation(text);
        if (calculation) {
            return {
                type: 'calculation',
                message: calculation,
            };
        }

        if (/^(open|launch|start|run)\s+/.test(normalized)) {
            const target = normalized.replace(/^(open|launch|start|run)\s+/, '').trim();
            const displayTarget = text.replace(/^(open|launch|start|run)\s+/i, '').trim();

            if (websiteAliases[target]) {
                window.open(websiteAliases[target], '_blank');
                return { type: 'response', message: `Opening ${displayTarget}.` };
            }

            if (/^https?:\/\//i.test(displayTarget)) {
                window.open(displayTarget, '_blank');
                return { type: 'response', message: `Opening ${displayTarget}.` };
            }

            if (target.includes('.') && !target.includes(' ')) {
                window.open(`https://${target}`, '_blank');
                return { type: 'response', message: `Opening ${displayTarget}.` };
            }

            if (browserAppNames.has(target)) {
                return {
                    type: 'response',
                    message: 'Local core is offline. Start Jarvis Core to control Windows apps.',
                };
            }
        }

        if (/^(search|google)\s+/.test(normalized)) {
            const query = text.replace(/^(search|google)\s+/i, '').trim();
            if (!query) {
                return { type: 'response', message: 'Tell me what to search for.' };
            }
            const engineUrl = normalized.startsWith('google ')
                ? `https://www.google.com/search?q=${encodeURIComponent(query)}`
                : `https://duckduckgo.com/?q=${encodeURIComponent(query)}`;
            window.open(engineUrl, '_blank');
            return { type: 'response', message: `Opening browser fallback search for ${query}. Start Local Core for DDGS/SearXNG results inside Jarvis.` };
        }

        if (/^(read|summarize).*(https?:\/\/\S+|www\.\S+\.\S+)/i.test(text)) {
            return {
                type: 'response',
                message: 'Start the local core to read links safely, or open the link and ask again from Jarvis Core.',
            };
        }

        if (/^(train skills|install skills|train skill pack|install skill pack|retrain skills|refresh skills|skill status|skills status|list skills|show skills)$/.test(normalized)) {
            return {
                type: 'training',
                message: 'Start Jarvis with START_JARVIS.bat so Local Core can save skill packs into the brain. Browser-only mode can use built-in temporary skill rules for answers and code, but it cannot write the trained skill memory.',
            };
        }

        if (/^(train model|train brain|train jarvis|retrain model|train my model|build model)$/.test(normalized)) {
            return {
                type: 'training',
                message: 'Start the local core to train the local brain. Browser-only mode cannot save the model files.',
            };
        }

        if (/^(add link|learn link|train from link|add url|learn url)\b/i.test(text)) {
            return {
                type: 'training',
                message: 'Start the local core to read and save link knowledge.',
            };
        }

        if (/^(add knowledge|learn knowledge|remember knowledge|train from text|learn this)\b/i.test(text)) {
            return {
                type: 'training',
                message: 'Start the local core to save training text into Jarvis memory.',
            };
        }

        if (/^(train|learn)\s+from\s+(dataset|kaggle|github)\b/i.test(text) || /^(add|import)\s+(dataset|github)\b/i.test(text) || /^kaggle\s+dataset\b/i.test(text)) {
            return {
                type: 'training',
                message: 'Start the local core to import datasets and GitHub README/raw links safely into RAG memory. Browser-only mode cannot save trained knowledge.',
            };
        }

        if (/^(ask|query)\s+(knowledge|brain|rag)\b/i.test(text) || /^(knowledge|brain|rag)\s+question\b/i.test(text)) {
            return {
                type: 'rag',
                message: 'Start the local core to answer from saved RAG knowledge.',
            };
        }

        if (normalized.includes('wikipedia')) {
            const topic = text.replace(/open|read|search|wikipedia|of|about/ig, ' ').replace(/\s+/g, ' ').trim();
            if (topic) {
                window.open(`https://en.wikipedia.org/wiki/${encodeURIComponent(topic.replace(/\s+/g, '_'))}`, '_blank');
                return { type: 'response', message: `Opening Wikipedia for ${topic}. Local core can read the summary aloud.` };
            }
        }

        if (isNewsCommand(text)) {
            const message = [
                'Local Core is not running on port 8765, so DDGS/SearXNG briefing is unavailable in this browser tab.',
                `Backend URL: ${bridgeUrl}`,
                restartInstruction,
                'No Google News fallback was opened automatically. Start Local Core for the free local search stack.',
            ].join('\n');
            return {
                type: 'briefing',
                message,
                briefing: { message, sections: [] },
            };
        }

        const directShareMatch = normalized.includes('email') ? null : text.match(/(?:send|share)\s+(?:to|on)\s+(.+?)\s+(?:message|text|body)\s+(.+)$/i);
        const shareMatch = directShareMatch || (normalized.includes('email') ? null : text.match(/(?:send|share)\s+(.+?)\s+(?:to|on)\s+(.+)$/i));
        if (shareMatch) {
            const numberMatch = text.match(/(?:number|phone|to)\s+(\+?\d[\d\s-]{7,})/i);
            const number = numberMatch ? numberMatch[1].trim() : '';
            const target = directShareMatch ? shareMatch[1].trim() : shareMatch[2].trim().replace(/\s+(?:number|phone|to)\s+\+?\d[\d\s-]{7,}.*$/i, '').trim();
            const message = directShareMatch ? shareMatch[2].trim() : shareMatch[1].trim();
            return {
                type: 'confirm_share',
                message: `Ready to share to ${target}.`,
                share: {
                    message,
                    target,
                    number,
                },
                browserOnly: true,
            };
        }

        if (/^(just\s+)?scroll(\s+(down|up))?$/.test(normalized)) {
            window.scrollBy({ top: normalized.includes('up') ? -420 : 420, behavior: 'smooth' });
            return { type: 'response', message: normalized.includes('up') ? 'Scrolled up.' : 'Scrolled down.' };
        }

        if (normalized.includes('scroll shorts') || normalized.includes('scroll the shorts') || normalized.includes('auto scroll') || normalized.includes('start scrolling') || normalized.includes('keep scrolling')) {
            window.open('https://www.youtube.com/shorts', '_blank');
            return {
                type: 'confirm_action',
                action: 'auto_scroll',
                message: 'Local core can auto-scroll the focused Shorts window after approval.',
            };
        }

        if (/^(terminal|run command|run terminal|shell|cmd)\s+/.test(text)) {
            const command = text.replace(/^(terminal|run command|run terminal|shell|cmd)\s+/i, '');
            return {
                type: 'confirm_terminal',
                message: `Run terminal command: ${command}`,
                terminal: { command },
                browserOnly: true,
            };
        }

        if ((normalized.includes('code') || normalized.includes('program')) && /(write|create|generate|make)/.test(normalized)) {
            return {
                type: 'code',
                message: localCodeFromPrompt(text),
            };
        }

        if (/\bplay\b/.test(normalized) && normalized.includes('youtube')) {
            const query = text.replace(/\bplay\b/ig, '').replace(/\bon youtube\b/ig, '').replace(/\byoutube\b/ig, '').trim();
            if (!query) {
                return { type: 'response', message: 'Tell me what to play on YouTube.' };
            }
            window.open(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`, '_blank');
            return { type: 'response', message: `Searching YouTube for ${query}.` };
        }

        if (/\bjoke\b/.test(normalized)) {
            const jokes = [
                'I would tell you a UDP joke, but you might not get it.',
                'Why did the programmer quit his job? Because he did not get arrays.',
                'I only know 25 letters of the alphabet. I do not know y.',
            ];
            return { type: 'response', message: jokes[Math.floor(Math.random() * jokes.length)] };
        }

        if (/\b(send|compose|write|draft)\s+(an\s+)?email\b/.test(normalized)) {
            const email = parseEmailRequest(text);
            if (!email.to) {
                return { type: 'response', message: 'Tell me who the email should go to.' };
            }
            if (!email.body) {
                return { type: 'response', message: 'Tell me the email body.' };
            }
            return {
                type: 'confirm_email',
                message: `Ready to prepare email to ${email.to} with subject ${email.subject}.`,
                email,
                browserOnly: true,
            };
        }

        if (/^(write note|take note|remember)\s+/.test(normalized)) {
            const note = text.replace(/^(write note|take note|remember)\s+/i, '').trim();
            const notes = JSON.parse(localStorage.getItem('jarvis-notes') || '[]');
            notes.push({ at: new Date().toISOString(), text: note });
            localStorage.setItem('jarvis-notes', JSON.stringify(notes.slice(-50)));
            return { type: 'response', message: 'Note saved.' };
        }

        if (/^(read notes|read note|show notes|show my notes)$/.test(normalized)) {
            const notes = JSON.parse(localStorage.getItem('jarvis-notes') || '[]');
            if (!notes.length) {
                return { type: 'response', message: 'There are no saved notes yet.' };
            }
            return {
                type: 'response',
                message: 'Here are the latest notes. ' + notes.slice(-5).map((item) => item.text).join(' '),
            };
        }

        if (/^(read aloud|speak)\s+/.test(normalized)) {
            const speech = text.replace(/^(read aloud|speak)\s+/i, '').trim();
            speakText(speech);
            return { type: 'response', message: speech };
        }

        if (/^(write file|read file)\s+/.test(normalized)) {
            return {
                type: 'response',
                message: 'Local core is offline. Start Jarvis Core to read and write files.',
            };
        }

        const topic = extractGeneralTopic(text);
        if (topic) {
            window.open(`https://duckduckgo.com/?q=${encodeURIComponent(topic)}`, '_blank');
            return {
                type: 'answer',
                message: [
                    `I opened live search results for ${topic}. Start Jarvis from START_JARVIS.bat for a stronger direct answer with local retrieval.`,
                ].join('\n'),
            };
        }

        return {
            type: 'response',
            message: 'I can answer questions, search category news, write code, open apps, read links, draft email with approval, and save notes. For Jarvis support, contact mdwasiullah445@gmail.com.',
        };
    }

    function titleFromPrompt(command, fallback = 'Jarvis Website') {
        const cleaned = command
            .toLowerCase()
            .replace(/\b(write|create|generate|make|code|program|script|for|a|an|my|the|using|with|in|html|css|javascript|js|react|nextjs|next\.js|next|python|website|webpage|web page|web site|site|app|improved|polished|responsive|version)\b/g, ' ')
            .replace(/[^a-z0-9 ]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
        const words = cleaned.split(' ').filter(Boolean).slice(0, 4);
        if (!words.length) {
            return fallback;
        }
        return words.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
    }

    function componentNameFromTitle(title) {
        const name = title.replace(/[^a-zA-Z0-9]+/g, ' ').trim().split(/\s+/)
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join('');
        return name || 'GeneratedApp';
    }

    function reactCodeFromPrompt(command, title, kind) {
        const componentName = componentNameFromTitle(title);
        if (kind === 'task') {
            return `\`\`\`jsx
import { useMemo, useState } from "react";

export default function TaskManager() {
  const [items, setItems] = useState([]);
  const [text, setText] = useState("");
  const completed = useMemo(() => items.filter((item) => item.done).length, [items]);

  function addTask(event) {
    event.preventDefault();
    if (!text.trim()) return;
    setItems([...items, { id: crypto.randomUUID(), title: text.trim(), done: false }]);
    setText("");
  }

  return (
    <main className="min-h-screen bg-slate-100 p-6 text-slate-950">
      <section className="mx-auto grid max-w-2xl gap-4 rounded-2xl bg-white p-6 shadow-xl">
        <header>
          <h1 className="text-4xl font-bold">Task Manager</h1>
          <p className="text-slate-500">{completed} of {items.length} completed</p>
        </header>
        <form onSubmit={addTask} className="flex gap-2">
          <input className="min-w-0 flex-1 rounded-xl border p-3" value={text} onChange={(event) => setText(event.target.value)} placeholder="Add a task" />
          <button className="rounded-xl bg-blue-600 px-4 font-bold text-white">Add</button>
        </form>
        <div className="grid gap-2">
          {items.map((item) => (
            <button key={item.id} onClick={() => setItems(items.map((task) => task.id === item.id ? { ...task, done: !task.done } : task))} className="rounded-xl bg-slate-50 p-3 text-left">
              <span className={item.done ? "line-through opacity-50" : ""}>{item.title}</span>
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
\`\`\``;
        }

        return `\`\`\`jsx
import { useMemo, useState } from "react";

export default function ${componentName}() {
  const [value, setValue] = useState("");
  const output = useMemo(() => value.trim() || "Start typing to generate a result.", [value]);

  return (
    <main className="grid min-h-screen place-items-center bg-zinc-100 p-6 text-zinc-950">
      <section className="grid w-full max-w-3xl gap-5 rounded-2xl bg-white p-6 shadow-xl">
        <header>
          <h1 className="text-4xl font-bold">${title}</h1>
          <p className="text-zinc-500">Responsive React app generated from your prompt.</p>
        </header>
        <textarea className="min-h-32 rounded-xl border p-4" value={value} onChange={(event) => setValue(event.target.value)} placeholder="Type here" />
        <article className="rounded-xl bg-zinc-50 p-4">{output}</article>
      </section>
    </main>
  );
}
\`\`\``;
    }

    function nextCodeFromPrompt(command, title, kind) {
        const component = reactCodeFromPrompt(command, title, kind)
            .replace('```jsx', '```tsx')
            .replace(/import \{ useMemo, useState \} from "react";\n\n/, '"use client";\n\nimport { useMemo, useState } from "react";\n\n');
        return component;
    }

    function localCodeFromPrompt(command) {
        const normalized = command.toLowerCase();
        const wantsReact = /\breact\b/.test(normalized);
        const wantsNext = /\b(nextjs|next\.js|next)\b/.test(normalized);
        const wantsPython = /\bpython\b/.test(normalized);
        const wantsJs = /\b(javascript|js)\b/.test(normalized);
        const isNameFixer = normalized.includes('name fixer');
        const isTodo = /\b(todo|task manager|task app)\b/.test(normalized);
        const isPortfolio = /\b(portfolio|personal website)\b/.test(normalized);
        const isLogin = /\b(login|sign in|signin)\b/.test(normalized);
        const isCalculator = normalized.includes('calculator');
        const promptTitle = isNameFixer ? 'Name Fixer' : isTodo ? 'Task Manager' : isPortfolio ? 'Portfolio' : isLogin ? 'Login Portal' : isCalculator ? 'Calculator' : titleFromPrompt(command);
        const promptKind = isTodo ? 'task' : isPortfolio ? 'portfolio' : isLogin ? 'login' : isNameFixer ? 'name' : 'generic';

        if (wantsNext && !isNameFixer) {
            return nextCodeFromPrompt(command, promptTitle, promptKind);
        }

        if (wantsReact && !isNameFixer) {
            return reactCodeFromPrompt(command, promptTitle, promptKind);
        }

        if (wantsNext) {
            return `\`\`\`tsx
export default function Page() {
  const features = ["Fast local replies", "Preview-ready UI", "Secure actions"];

  return (
    <main className="min-h-screen bg-neutral-950 px-6 py-12 text-white">
      <section className="mx-auto grid max-w-5xl gap-8">
        <div className="grid gap-4">
          <p className="text-sm font-semibold uppercase tracking-wide text-emerald-300">Next.js</p>
          <h1 className="text-4xl font-bold md:text-6xl">Name Fixer</h1>
          <p className="max-w-2xl text-neutral-300">
            Clean messy names into display names, usernames, initials, and URL-safe slugs.
          </p>
        </div>

        <div className="grid gap-4 rounded-2xl border border-white/10 bg-white/5 p-6">
          <input
            className="rounded-xl border border-white/10 bg-neutral-900 p-4 outline-none"
            placeholder="md WASI__portfolio site"
          />
          <div className="grid gap-3 md:grid-cols-3">
            {features.map((feature) => (
              <div key={feature} className="rounded-xl bg-white/10 p-4">{feature}</div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
\`\`\``;
        }

        if (wantsReact) {
            return `\`\`\`jsx
import { useMemo, useState } from "react";

export default function NameFixer() {
  const [value, setValue] = useState("");
  const output = useMemo(() => {
    const words = value.replace(/[_-]+/g, " ").replace(/[^a-zA-Z0-9 ]+/g, "").trim().split(/\\s+/).filter(Boolean);
    const title = words.map((word) => word[0]?.toUpperCase() + word.slice(1).toLowerCase()).join(" ");
    return {
      title,
      initials: words.map((word) => word[0]?.toUpperCase()).join(""),
      username: words.map((word) => word.toLowerCase()).join(""),
      slug: words.map((word) => word.toLowerCase()).join("-"),
    };
  }, [value]);

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 p-6">
      <section className="grid w-full max-w-2xl gap-4 rounded-2xl bg-white p-6 shadow-xl">
        <h1 className="text-4xl font-bold">Name Fixer</h1>
        <textarea value={value} onChange={(event) => setValue(event.target.value)} placeholder="md WASI__portfolio site" />
        {Object.entries(output).map(([label, text]) => (
          <div key={label} className="rounded-xl bg-slate-50 p-3">
            <strong>{label}</strong>
            <p>{text || "Waiting..."}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
\`\`\``;
        }

        if (wantsPython && isNameFixer) {
            return `\`\`\`python
import re


def fix_name(value: str) -> dict[str, str]:
    words = re.sub(r"[_-]+", " ", value)
    words = re.sub(r"[^a-zA-Z0-9 ]+", "", words).strip().split()
    title = " ".join(word.capitalize() for word in words)
    return {
        "display_name": title,
        "initials": "".join(word[0].upper() for word in words),
        "username": "".join(word.lower() for word in words),
        "slug": "-".join(word.lower() for word in words),
    }


if __name__ == "__main__":
    raw = input("Enter messy name: ")
    for key, value in fix_name(raw).items():
        print(f"{key}: {value}")
\`\`\``;
        }

        if (wantsPython && isTodo) {
            return `\`\`\`python
from dataclasses import dataclass


@dataclass
class Task:
    title: str
    done: bool = False


class TaskManager:
    def __init__(self):
        self.tasks: list[Task] = []

    def add(self, title: str) -> None:
        self.tasks.append(Task(title.strip()))

    def complete(self, index: int) -> None:
        self.tasks[index].done = True

    def list_tasks(self) -> None:
        for index, task in enumerate(self.tasks, start=1):
            status = "done" if task.done else "open"
            print(f"{index}. [{status}] {task.title}")


if __name__ == "__main__":
    manager = TaskManager()
    manager.add("Build Jarvis")
    manager.add("Test voice input")
    manager.complete(0)
    manager.list_tasks()
\`\`\``;
        }

        if (wantsPython) {
            return `\`\`\`python
def main():
    user_input = input("Enter text: ").strip()
    cleaned = " ".join(user_input.split())
    print(f"Processed result: {cleaned}")


if __name__ == "__main__":
    main()
\`\`\``;
        }

        if (wantsJs && isTodo && !normalized.includes('html')) {
            return `\`\`\`javascript
const tasks = [];

function addTask(title) {
  if (!title.trim()) return;
  tasks.push({ id: crypto.randomUUID(), title: title.trim(), done: false });
}

function toggleTask(id) {
  const task = tasks.find((item) => item.id === id);
  if (task) task.done = !task.done;
}

function listTasks() {
  return tasks.map((task, index) => \`\${index + 1}. [\${task.done ? "done" : "open"}] \${task.title}\`);
}

addTask("Build Jarvis");
addTask("Test code writer");
toggleTask(tasks[0].id);
console.log(listTasks().join("\\n"));
\`\`\``;
        }

        if (wantsJs && !normalized.includes('html')) {
            return `\`\`\`javascript
function fixName(value) {
  const words = value
    .replace(/[_-]+/g, " ")
    .replace(/[^a-zA-Z0-9 ]+/g, "")
    .trim()
    .split(/\\s+/)
    .filter(Boolean);

  return {
    title: words.map((word) => word[0].toUpperCase() + word.slice(1).toLowerCase()).join(" "),
    initials: words.map((word) => word[0].toUpperCase()).join(""),
    username: words.map((word) => word.toLowerCase()).join(""),
    slug: words.map((word) => word.toLowerCase()).join("-"),
  };
}

console.log(fixName("md WASI__portfolio site"));
\`\`\``;
        }

        if (isCalculator) {
            return `\`\`\`html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Calculator</title>
  <style>
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; font-family: system-ui, sans-serif; background: #111827; }
    main { width: min(340px, 92vw); display: grid; gap: 10px; padding: 18px; border-radius: 18px; background: #f8fafc; }
    input { height: 56px; padding: 0 12px; border: 1px solid #d1d5db; border-radius: 10px; text-align: right; font-size: 1.6rem; }
    .keys { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
    button { min-height: 48px; border: 0; border-radius: 10px; background: #e5e7eb; font-size: 1rem; font-weight: 700; }
    .op { background: #10b981; color: white; }
  </style>
</head>
<body>
  <main>
    <input id="display" value="0" readonly>
    <section class="keys" id="keys"></section>
  </main>
  <script>
    const keys = ["C", "(", ")", "/", "7", "8", "9", "*", "4", "5", "6", "-", "1", "2", "3", "+", "0", ".", "⌫", "="];
    const display = document.querySelector("#display");
    document.querySelector("#keys").innerHTML = keys.map((key) => '<button class="' + ("+-*/=".includes(key) ? "op" : "") + '">' + key + '</button>').join("");
    document.querySelector("#keys").addEventListener("click", (event) => {
      const key = event.target.textContent;
      if (key === "C") display.value = "0";
      else if (key === "⌫") display.value = display.value.slice(0, -1) || "0";
      else if (key === "=") display.value = /^[0-9+\\-*/(). ]+$/.test(display.value) ? String(Function("return " + display.value)()) : "Error";
      else display.value = display.value === "0" ? key : display.value + key;
    });
  </script>
</body>
</html>
\`\`\``;
        }

        if (isTodo) {
            return buildWebsiteTemplate('Task Manager', 'Add, complete, and filter your daily tasks.', 'task');
        }
        if (isPortfolio) {
            return buildWebsiteTemplate('Portfolio', 'Showcase projects, skills, and contact details.', 'portfolio');
        }
        if (isLogin) {
            return buildWebsiteTemplate('Login Portal', 'Clean sign-in form with client-side validation.', 'login');
        }
        if (isNameFixer) {
            return buildWebsiteTemplate('Name Fixer', 'Paste a messy name and get title case, initials, username, slug, and file-safe output.', 'name');
        }
        if (normalized.includes('website') || normalized.includes('web page') || normalized.includes('site')) {
            return buildWebsiteTemplate(promptTitle, `A responsive ${promptTitle} website generated from your prompt.`, promptKind);
        }
        if (normalized.includes('html')) {
            return buildWebsiteTemplate(promptTitle, `A clean responsive ${promptTitle} page.`, promptKind);
        }
        return `\`\`\`python
def main():
    print("Tell me the language, for example: HTML, React, Next.js, Python, or JavaScript.")


if __name__ == "__main__":
    main()
\`\`\``;
    }

    function buildWebsiteTemplate(title, subtitle, kind) {
        const extra = kind === 'task'
            ? '<input id="itemInput" placeholder="Add a task"><button id="addBtn">Add task</button><ul id="list"></ul>'
            : kind === 'login'
                ? '<input placeholder="Email"><input type="password" placeholder="Password"><button>Sign in</button>'
                : kind === 'portfolio'
                    ? '<div class="grid"><article><span>Project</span><strong>Jarvis Assistant</strong><p>Secure desktop automation, code writing, and daily briefing tools.</p></article><article><span>Skill</span><strong>Frontend + AI</strong><p>Responsive UI, local actions, and safe approval flows.</p></article><article><span>Contact</span><strong>hello@example.com</strong><p>Replace this with your real contact details.</p></article></div>'
                    : kind === 'generic'
                        ? '<div class="grid"><article><span>Feature</span><strong>Fast</strong><p>Designed to load quickly and work on mobile.</p></article><article><span>Feature</span><strong>Responsive</strong><p>The layout adapts cleanly across screen sizes.</p></article><article><span>Feature</span><strong>Ready</strong><p>Edit the content and connect your own logic.</p></article></div>'
                        : '<textarea id="nameInput" placeholder="Example: md WASI__portfolio site"></textarea><div class="actions"><button id="fixBtn">Fix name</button><button id="clearBtn" class="secondary">Clear</button></div><section id="results"></section>';

        const script = kind === 'task'
            ? 'const input=document.querySelector("#itemInput");const list=document.querySelector("#list");document.querySelector("#addBtn").onclick=()=>{if(!input.value.trim())return;const item=document.createElement("li");item.textContent=input.value;item.onclick=()=>item.classList.toggle("done");list.appendChild(item);input.value="";};'
            : kind === 'name'
                ? 'const input=document.querySelector("#nameInput");const results=document.querySelector("#results");function render(){const words=input.value.replace(/[_-]+/g," ").replace(/[^a-zA-Z0-9 ]+/g,"").trim().split(/\\\\s+/).filter(Boolean);if(!words.length){results.innerHTML="<p>Type a name to fix it.</p>";return;}const title=words.map(w=>w[0].toUpperCase()+w.slice(1).toLowerCase()).join(" ");const slug=words.map(w=>w.toLowerCase()).join("-");results.innerHTML=`<div class="result"><span>Best display name</span><strong>${title}</strong></div><div class="result"><span>Website slug</span><strong>${slug}</strong></div>`;}document.querySelector("#fixBtn").onclick=render;document.querySelector("#clearBtn").onclick=()=>{input.value="";render();};input.oninput=render;render();'
                : kind === 'generic' || kind === 'portfolio'
                    ? 'document.querySelectorAll("article").forEach((card)=>card.addEventListener("click",()=>card.classList.toggle("selected")));'
                    : '';

        return `\`\`\`html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${title}</title>
    <style>
      * { box-sizing: border-box; }
      body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px; font-family: Inter, system-ui, sans-serif; color: #17202a; background: #f4f6f8; }
      main { width: min(760px, 100%); display: grid; gap: 18px; }
      .panel { padding: 22px; border: 1px solid #dde3ea; border-radius: 14px; background: white; box-shadow: 0 20px 48px rgba(31, 41, 55, 0.08); }
      h1 { margin: 0 0 6px; font-size: clamp(2rem, 6vw, 3.5rem); }
      p { margin: 0; color: #667085; line-height: 1.5; }
      input, textarea { width: 100%; min-height: 44px; margin-top: 14px; padding: 12px; border: 1px solid #ccd5df; border-radius: 10px; font: inherit; }
      textarea { min-height: 132px; resize: vertical; }
      .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
      button { min-height: 40px; padding: 10px 14px; border: 0; border-radius: 10px; color: white; background: #1473e6; cursor: pointer; font-weight: 700; }
      button.secondary { color: #17202a; background: #edf2f7; }
      #results, ul { display: grid; gap: 10px; padding: 0; list-style: none; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-top: 16px; }
      li, .result, article { display: grid; gap: 4px; padding: 14px; border: 1px solid #e4e7ec; border-radius: 10px; background: #fbfcfd; }
      .done { text-decoration: line-through; opacity: .55; }
      .selected { border-color: #1473e6; box-shadow: 0 0 0 3px rgba(20, 115, 230, .12); }
      .result span, article span { color: #667085; font-size: 0.85rem; font-weight: 700; }
      .result strong, article strong { overflow-wrap: anywhere; }
    </style>
  </head>
  <body>
    <main>
      <section class="panel">
        <h1>${title}</h1>
        <p>${subtitle}</p>
        ${extra}
      </section>
    </main>
    <script>
      ${script}
    </script>
  </body>
</html>
\`\`\``;
    }

    function renderApprovalDetails(parsed) {
        approvalDetails.replaceChildren();

        const rows = [];
        if (parsed.type === 'confirm_email' && parsed.email) {
            rows.push(['To', parsed.email.to || '']);
            rows.push(['Subject', parsed.email.subject || '']);
            rows.push(['Body', parsed.email.body || '']);
        } else if (parsed.type === 'confirm_share' && parsed.share) {
            rows.push(['To', parsed.share.target || '']);
            if (parsed.share.number) {
                rows.push(['Number', parsed.share.number || '']);
            }
            rows.push(['Message', parsed.share.message || '']);
        } else if (parsed.type === 'confirm_terminal' && parsed.terminal) {
            rows.push(['Run', parsed.terminal.command || '']);
        } else if (parsed.type === 'confirm_action') {
            rows.push(['Action', parsed.action || 'action']);
            if (parsed.target) rows.push(['Target', parsed.target]);
            if (parsed.plan) {
                rows.push(['Intent', parsed.plan.intent || 'task']);
                rows.push(['Risk', (parsed.plan.risk || 'medium').toUpperCase()]);
                rows.push(['Summary', parsed.plan.summary || parsed.message || '']);
                if (Array.isArray(parsed.plan.steps)) {
                    rows.push(['Plan', parsed.plan.steps.join(' -> ')]);
                }
            }
        }

        rows.forEach(([label, value]) => {
            const dt = document.createElement('dt');
            dt.textContent = label;
            const dd = document.createElement('dd');
            dd.textContent = value;
            approvalDetails.append(dt, dd);
        });
    }

    function showApproval(parsed) {
        const isEmail = parsed.type === 'confirm_email';
        const isShare = parsed.type === 'confirm_share';
        const isTerminal = parsed.type === 'confirm_terminal';
        pendingApproval = {
            type: parsed.type,
            email: parsed.email || null,
            share: parsed.share || null,
            terminal: parsed.terminal || null,
            plan: parsed.plan || null,
            confirmCommand: isEmail ? 'confirm send email' : (isShare ? 'confirm share' : (isTerminal ? 'confirm terminal' : `confirm ${(parsed.action || 'action').replace('_', ' ')}`)),
            cancelCommand: isEmail ? 'cancel email' : (isShare ? 'cancel share' : (isTerminal ? 'cancel action' : `cancel ${(parsed.action || 'action').replace('_', ' ')}`)),
            browserOnly: Boolean(parsed.browserOnly),
        };

        approvalMessage.textContent = parsed.message || 'Confirm this action.';
        renderApprovalDetails(parsed);
        approvalPanel.classList.remove('hidden');
        setMode('Approval');
        addToConsole(parsed.message || 'Permission required.', 'system');
        speakText(parsed.message || 'Permission required.');
    }

    function hideApproval() {
        pendingApproval = null;
        approvalPanel.classList.add('hidden');
        approvalDetails.replaceChildren();
    }

    function sendBrowserEmail(email) {
        const url = `mailto:${encodeURIComponent(email.to)}?subject=${encodeURIComponent(email.subject || '')}&body=${encodeURIComponent(email.body || '')}`;
        window.location.href = url;
        return 'Email draft opened for final review.';
    }

    function sendBrowserShare(share) {
        const target = (share.target || '').toLowerCase();
        const message = share.message || '';
        const number = String(share.number || currentSettings.whatsapp_number || '').replace(/\D/g, '');
        if (target.includes('whatsapp')) {
            const url = number ? `https://wa.me/${number}?text=${encodeURIComponent(message)}` : `https://wa.me/?text=${encodeURIComponent(message)}`;
            window.open(url, '_blank');
            return 'WhatsApp share draft opened for final review.';
        }
        if (target.includes('email') || target.includes('gmail')) {
            window.location.href = `mailto:?subject=Jarvis briefing&body=${encodeURIComponent(message)}`;
            return 'Email share draft opened for final review.';
        }
        window.open(`https://www.google.com/search?q=${encodeURIComponent(share.target || '')}`, '_blank');
        return 'Share target opened for final review.';
    }

    function runBrowserTerminal(command) {
        terminalOutput.textContent = `Safe mode cannot run shell commands directly.\nStart Local Core, then approve this command again:\n${command}`;
        return 'Terminal needs Local Core for command execution.';
    }

    async function approvePendingAction() {
        if (!pendingApproval || isBusy) {
            return;
        }

        const approval = pendingApproval;
        hideApproval();
        setBusy(true);

        try {
            let response;
            if (approval.browserOnly && approval.type === 'confirm_email') {
                response = { type: 'response', message: sendBrowserEmail(approval.email) };
            } else if (approval.browserOnly && approval.type === 'confirm_share') {
                response = { type: 'response', message: sendBrowserShare(approval.share) };
            } else if (approval.browserOnly && approval.type === 'confirm_terminal') {
                response = { type: 'terminal', message: runBrowserTerminal(approval.terminal?.command || '') };
            } else {
                response = tryParseJson(await callAssistant(approval.confirmCommand));
            }
            handleAssistantResponse(response, approval.confirmCommand);
        } catch (error) {
            addToConsole('Action failed.', 'error');
            speakText('Action failed.');
        } finally {
            setBusy(false);
        }
    }

    async function cancelPendingAction() {
        if (!pendingApproval || isBusy) {
            return;
        }

        const approval = pendingApproval;
        hideApproval();

        if (!approval.browserOnly) {
            try {
                await callAssistant(approval.cancelCommand);
            } catch (error) {
                // The UI cancellation is already complete.
            }
        }

        addToConsole('Action canceled.', 'system');
        speakText('Action canceled.');
        setMode('Ready');
    }

    function handleAssistantResponse(response, originalCommand) {
        removeThinking();
        const parsed = tryParseJson(response);

        if (parsed && typeof parsed === 'object') {
            if (parsed.type === 'confirm_email' || parsed.type === 'confirm_action' || parsed.type === 'confirm_share' || parsed.type === 'confirm_terminal') {
                showApproval(parsed);
                return;
            }

            const message = parsed.message || 'Command complete.';
            const displayMessage = cleanAssistantText(message);
            rememberGeneratedCode(message, originalCommand);
            if (parsed.type === 'briefing') {
                lastBriefingMessage = cleanAssistantText(parsed.briefing?.message || message);
            }
            if (parsed.type === 'terminal') {
                terminalOutput.textContent = message;
            }
            if (parsed.type === 'training' || parsed.type === 'rag') {
                trainingStatus.textContent = displayMessage;
            }
            if (parsed.corrected) {
                addToConsole(`Corrected command: ${parsed.corrected}`, 'system');
            }
            const tone = parsed.type === 'error' ? 'error' : 'jarvis';
            addToConsole(displayMessage, tone);
            setLiveTranscript(displayMessage);
            speakText(displayMessage);

            if (parsed.close || /^(exit|close jarvis|close app)$/i.test(originalCommand || '')) {
                setTimeout(() => window.close(), 900);
            }
            return;
        }

        const message = String(parsed || 'Command complete.');
        const displayMessage = cleanAssistantText(message);
        rememberGeneratedCode(message, originalCommand);
        addToConsole(displayMessage, 'jarvis');
        setLiveTranscript(displayMessage);
        speakText(displayMessage);
    }

    async function processCommand(command) {
        const text = normalize(command);
        if (!text || isBusy) {
            return;
        }

        if (pendingApproval && /^(approve|approved|yes|confirm|ok|okay|do it|continue)$/i.test(text)) {
            await approvePendingAction();
            return;
        }

        if (pendingApproval && /^(cancel|reject|no|stop)$/i.test(text)) {
            await cancelPendingAction();
            return;
        }

        hideApproval();
        setBusy(true);
        setLiveTranscript(text);
        document.body.classList.add('chat-started');
        addToConsole(text, 'user');
        rememberHistory(text);
        showThinking();

        try {
            const response = await callAssistant(text);
            handleAssistantResponse(response, text);
        } catch (error) {
            removeThinking();
            const message = 'Local core did not respond. Safe browser mode is still active.';
            addToConsole(message, 'error');
            setLiveTranscript(message);
            speakText(message);
        } finally {
            setBusy(false);
            commandInput.focus();
        }
    }

    async function startListening() {
        if (location.protocol === 'file:') {
            if (await canServeVoicePage()) {
                const voiceUrl = `${bridgeUrl}/index.html`;
                addToConsole('Opening Jarvis voice mode on localhost. Allow microphone when the browser asks.', 'system');
                window.location.href = voiceUrl;
                return;
            }

            const voiceHelp = 'Microphone is blocked because this page is open as a file. Start or restart Jarvis with START_JARVIS.bat, then open http://127.0.0.1:8765/index.html and allow microphone access.';
            addToConsole(voiceHelp, 'error');
            setLiveTranscript(voiceHelp);
            voiceBadge.textContent = 'Voice Blocked';
            voiceBadge.classList.add('warn');
            voiceValue.textContent = 'BLOCKED';
            return;
        }

        if (!recognitionCtor) {
            addToConsole('Voice recognition is not supported in this browser.', 'error');
            return;
        }

        if (!recognitionInstance) {
            recognitionInstance = new recognitionCtor();
            recognitionInstance.lang = 'en-US';
            recognitionInstance.interimResults = true;
            recognitionInstance.continuous = false;
            recognitionInstance.maxAlternatives = 1;

            recognitionInstance.onstart = () => {
                isListening = true;
                voiceMuted = false;
                finalTranscript = '';
                micBtn.classList.add('listening');
                voiceBadge.textContent = 'Listening';
                voiceValue.textContent = 'LIVE';
                setMode('Listening');
                setLiveTranscript('Listening...');
                addToConsole('Voice capture started.', 'system');
            };

            recognitionInstance.onresult = (event) => {
                let interim = '';
                for (let index = event.resultIndex; index < event.results.length; index += 1) {
                    const transcript = event.results[index][0].transcript;
                    if (event.results[index].isFinal) {
                        finalTranscript += transcript;
                    } else {
                        interim += transcript;
                    }
                }

                const liveText = normalize(finalTranscript || interim);
                commandInput.value = liveText;
                setLiveTranscript(liveText || 'Listening...');
            };

            recognitionInstance.onerror = (event) => {
                isListening = false;
                micBtn.classList.remove('listening');
                voiceBadge.textContent = 'Voice Standby';
                voiceValue.textContent = 'READY';
                addToConsole(`Voice capture failed: ${event.error || 'microphone blocked'}.`, 'error');
                setMode('Ready');
            };

            recognitionInstance.onend = async () => {
                isListening = false;
                micBtn.classList.remove('listening');
                voiceBadge.textContent = 'Voice Standby';
                voiceValue.textContent = 'READY';

                const spokenCommand = normalize(finalTranscript);
                finalTranscript = '';
                if (spokenCommand) {
                    commandInput.value = '';
                    await processCommand(spokenCommand);
                } else {
                    setMode('Ready');
                    setLiveTranscript(commandInput.value);
                }
            };
        }

        if (isListening) {
            recognitionInstance.stop();
            return;
        }

        try {
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach((track) => track.stop());
            }
            recognitionInstance.start();
        } catch (error) {
            const voiceHelp = location.protocol === 'file:'
                ? 'Microphone is blocked because this page is open as a file. Start Jarvis with START_JARVIS.bat, then allow microphone in the browser permission popup.'
                : 'Microphone permission is blocked. Click the browser microphone permission icon, allow access, then press the mic again.';
            addToConsole(voiceHelp, 'error');
            setLiveTranscript(voiceHelp);
            voiceBadge.textContent = 'Voice Blocked';
            voiceBadge.classList.add('warn');
            voiceValue.textContent = 'BLOCKED';
        }
    }

    function applyConnectionLabels(label, connected) {
        backendBadge.textContent = label;
        backendBadge.classList.toggle('success', connected);
        backendBadge.classList.toggle('warn', !connected);
        aiValue.textContent = connected ? 'READY' : 'SAFE';
        if (connectionPanel) {
            connectionPanel.classList.toggle('hidden', connected);
        }
        if (connectionTitle) {
            connectionTitle.textContent = connected ? 'Local Core connected' : 'Local Core offline';
        }
        if (connectionDetails) {
            const pageMode = location.protocol === 'file:' ? 'file browser mode' : `${location.host} browser mode`;
            const stack = lastHealth?.search_stack;
            const pieces = stack
                ? ['DDGS', 'SearXNG', 'Crawl4AI', 'Playwright', 'BeautifulSoup']
                    .filter((name) => stack[name.toLowerCase()] || (name === 'BeautifulSoup' && stack.beautifulsoup))
                    .join(', ')
                : 'DDGS/SearXNG';
            connectionDetails.textContent = connected
                ? `Backend URL: ${bridgeUrl} · Page mode: ${pageMode} · Free search stack: ${pieces || 'fallback parser'} · RAG, scraping, and desktop actions are available.`
                : `Backend URL: ${bridgeUrl} · Page mode: ${pageMode} · ${restartInstruction}`;
        }
    }

    function showModule(moduleName) {
        const showSettings = moduleName === 'Settings';
        const showTerminal = moduleName === 'Terminal';
        settingsView.classList.toggle('hidden', !showSettings);
        terminalView.classList.toggle('hidden', !showTerminal);
        dashboardViews.forEach((view) => view.classList.toggle('hidden', showSettings || showTerminal));
        if (showSettings) {
            loadSettings();
        }
    }

    async function updateConnectionMode() {
        if (hasBackend()) {
            applyConnectionLabels('Desktop Core', true);
        } else if (await checkBridge()) {
            applyConnectionLabels('Local Core', true);
        } else {
            applyConnectionLabels('Safe Mode', false);
        }

        if (!recognitionCtor) {
            voiceBadge.textContent = 'Voice Off';
            voiceBadge.classList.remove('success');
            voiceBadge.classList.add('warn');
            voiceValue.textContent = 'OFF';
        }
    }

    function bindEvents() {
        modelPickerBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleFloatingMenu(modelMenu, modelPickerBtn);
        });

        sidebarToggle.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleSidebar();
        });

        if (mobileSidebarBtn) {
            mobileSidebarBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                toggleSidebar();
            });
        }

        brandGlyph.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleSidebar();
        });

        closePreviewBtn.addEventListener('click', closePreview);
        openPreviewBtn.addEventListener('click', openPreviewInNewPage);
        previewModal.addEventListener('click', (event) => {
            if (event.target === previewModal) {
                closePreview();
            }
        });

        plusMenuBtn.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleFloatingMenu(plusMenu, plusMenuBtn);
        });

        accountButton.addEventListener('click', (event) => {
            event.stopPropagation();
            toggleFloatingMenu(accountMenu, accountButton);
        });

        [modelMenu, plusMenu, accountMenu].forEach((menu) => {
            menu.addEventListener('click', (event) => {
                event.stopPropagation();
            });
        });

        document.addEventListener('click', (event) => {
            closeFloatingMenus();
            if (isMobileLayout() && sidebar && !sidebar.contains(event.target) && !(mobileSidebarBtn && mobileSidebarBtn.contains(event.target))) {
                document.body.classList.add('sidebar-collapsed');
            }
        });

        document.querySelectorAll('[data-settings-tab]').forEach((button) => {
            button.addEventListener('click', () => {
                showSettingsTab(button.dataset.settingsTab || 'General');
            });
        });

        document.querySelectorAll('[data-settings-shortcut]').forEach((button) => {
            button.addEventListener('click', () => {
                closeFloatingMenus();
                showModule('Settings');
                setMode('Settings');
                showSettingsTab(button.dataset.settingsShortcut || 'General');
                loadSettings();
            });
        });

        document.querySelectorAll('[data-menu-message]').forEach((button) => {
            button.addEventListener('click', () => {
                const message = button.dataset.menuMessage || 'Ready.';
                closeFloatingMenus();
                document.body.classList.add('chat-started');
                addToConsole(message, 'system');
                setLiveTranscript(message);
            });
        });

        document.querySelectorAll('[data-plus-action]').forEach((button) => {
            button.addEventListener('click', async () => {
                await runPlusAction(button.dataset.plusAction || '');
            });
        });

        document.querySelectorAll('[data-model-name]').forEach((button) => {
            button.addEventListener('click', () => {
                selectModel(button.dataset.modelName || 'JS 1');
            });
        });

        sendBtn.addEventListener('click', async () => {
            const command = commandInput.value;
            commandInput.value = '';
            await processCommand(command);
        });

        commandInput.addEventListener('keydown', async (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const command = commandInput.value;
                commandInput.value = '';
                await processCommand(command);
            }
        });

        commandInput.addEventListener('input', () => {
            setLiveTranscript(commandInput.value);
        });

        micBtn.addEventListener('click', startListening);
        stopVoiceBtn.addEventListener('click', async () => {
            stopVoice();
            await saveSettings({ voice_enabled: false });
        });
        approveBtn.addEventListener('click', approvePendingAction);
        cancelBtn.addEventListener('click', cancelPendingAction);

        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => {
                localStorage.setItem(historyStorageKey, JSON.stringify([]));
                renderHistory();
                addToConsole('History cleared.', 'system');
            });
        }

        document.querySelectorAll('[data-command]').forEach((button) => {
            button.addEventListener('click', async () => {
                const command = button.getAttribute('data-command') || '';
                commandInput.value = command;
                setLiveTranscript(command);
                const isTrainingShortcut = button.id === 'TopTrainBtn';
                if (isTrainingShortcut) {
                    setTopTrainingState(true);
                }
                try {
                    await processCommand(command);
                } finally {
                    if (isTrainingShortcut) {
                        setTopTrainingState(false);
                    }
                    commandInput.value = '';
                    closeFloatingMenus();
                    closeSidebarOnMobile();
                }
            });
        });

        document.querySelectorAll('[data-module]').forEach((button) => {
            button.addEventListener('click', () => {
                document.querySelectorAll('[data-module]').forEach((item) => item.classList.remove('active'));
                button.classList.add('active');
                const moduleName = button.getAttribute('data-module') || 'Dashboard';
                showModule(moduleName);
                if (moduleName === 'Dashboard' && button.textContent.trim().toLowerCase().includes('new chat')) {
                    resetChatSurface();
                    closeSidebarOnMobile();
                    return;
                }
                setMode(moduleName);
                if (moduleName === 'Security') {
                    setLiveTranscript('Security is high. Email, shutdown, and dangerous actions require permission.');
                } else if (moduleName === 'Settings') {
                    showSettingsTab('General');
                    setLiveTranscript('Settings locked to high-security local mode.');
                } else {
                    setLiveTranscript(`${moduleName} online.`);
                }
                addToConsole(`Module: ${moduleName}`, 'system');
                closeSidebarOnMobile();
            });
        });

        document.querySelectorAll('[data-mode]').forEach((button) => {
            button.addEventListener('click', async () => {
                const mode = button.dataset.mode || 'simple';
                document.querySelectorAll('[data-mode]').forEach((item) => item.classList.remove('active'));
                button.classList.add('active');
                await saveSettings({ work_mode: mode });
                const label = mode === 'full_access' ? 'Full Access' : mode.charAt(0).toUpperCase() + mode.slice(1);
                addToConsole(`${label} mode enabled. Security remains high.`, 'system');
            });
        });

        terminalRunBtn.addEventListener('click', async () => {
            const command = terminalInput.value.trim();
            if (!command) return;
            await processCommand(`terminal ${command}`);
        });

        terminalInput.addEventListener('keydown', async (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const command = terminalInput.value.trim();
                if (!command) return;
                await processCommand(`terminal ${command}`);
            }
        });

        saveApiBtn.addEventListener('click', async () => {
            apiStatus.textContent = 'Saving...';
            const updates = {
                api_enabled: apiEnabled.checked,
                api_endpoint: apiEndpointInput.value.trim() || 'https://api.openai.com/v1/chat/completions',
                api_model: apiModelInput.value.trim() || 'gpt-4o-mini',
                searxng_url: searxngUrlInput ? searxngUrlInput.value.trim() : '',
                ollama_model: ollamaModelInput.value.trim() || 'gemma3',
                whatsapp_number: whatsappNumberInput.value.trim(),
                work_mode: document.querySelector('[data-mode].active')?.dataset.mode || 'simple',
                voice_enabled: !voiceMuted,
                daily_briefing: dailyBriefingToggle.checked,
            };
            if (apiKeyInput.value.trim()) {
                updates.api_key = apiKeyInput.value.trim();
            }
            try {
                await saveSettings(updates);
                addToConsole('Settings saved.', 'system');
            } catch (error) {
                apiStatus.textContent = 'Settings save failed.';
                addToConsole('Settings save failed.', 'error');
            }
        });

        clearApiBtn.addEventListener('click', async () => {
            apiStatus.textContent = 'Clearing...';
            if (searxngUrlInput) {
                searxngUrlInput.value = '';
            }
            await saveSettings({ api_enabled: false, api_key: '', searxng_url: '' });
            addToConsole('Custom API cleared. Default local model and DDGS search active.', 'system');
        });

        dailyBriefingToggle.addEventListener('change', async () => {
            await saveSettings({
                daily_briefing: dailyBriefingToggle.checked,
                whatsapp_number: whatsappNumberInput.value.trim(),
                ollama_model: ollamaModelInput.value.trim() || 'gemma3',
            });
        });

        briefingBtn.addEventListener('click', async () => {
            await processCommand('daily briefing');
        });

        shareBriefingBtn.addEventListener('click', async () => {
            showApproval({
                type: 'confirm_share',
                message: 'Ready to share briefing to WhatsApp.',
                share: {
                    target: 'whatsapp',
                    message: lastBriefingMessage || 'Daily briefing is ready.',
                    number: whatsappNumberInput.value.trim(),
                },
                browserOnly: true,
            });
        });

        trainModelBtn.addEventListener('click', async () => {
            trainingStatus.textContent = 'Training local brain...';
            setTopTrainingState(true);
            try {
                await processCommand('train model');
            } finally {
                setTopTrainingState(false);
            }
        });

        addKnowledgeLinkBtn.addEventListener('click', async () => {
            const link = knowledgeLinkInput.value.trim();
            if (!link) {
                trainingStatus.textContent = 'Paste a link first.';
                return;
            }
            trainingStatus.textContent = 'Learning link...';
            await processCommand(`add link ${link}`);
        });

        addKnowledgeTextBtn.addEventListener('click', async () => {
            const lesson = knowledgeTextInput.value.trim();
            if (!lesson) {
                trainingStatus.textContent = 'Paste text first.';
                return;
            }
            trainingStatus.textContent = 'Saving lesson...';
            await processCommand(`add knowledge ${lesson}`);
        });

        importDatasetBtn.addEventListener('click', async () => {
            const dataset = datasetInput.value.trim();
            if (!dataset) {
                trainingStatus.textContent = 'Paste a dataset path, URL, or Kaggle slug first.';
                return;
            }
            trainingStatus.textContent = 'Importing dataset into RAG memory...';
            await processCommand(`train from dataset ${dataset}`);
        });

        askKnowledgeBtn.addEventListener('click', async () => {
            const question = knowledgeAskInput.value.trim();
            if (!question) {
                trainingStatus.textContent = 'Write a question first.';
                return;
            }
            await processCommand(`ask knowledge ${question}`);
        });

        knowledgeAskInput.addEventListener('keydown', async (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                const question = knowledgeAskInput.value.trim();
                if (!question) return;
                await processCommand(`ask knowledge ${question}`);
            }
        });

        brainTestBtn.addEventListener('click', async () => {
            await processCommand('opne claculator');
        });
    }

    function startTelemetry() {
        setInterval(() => {
            const nextValue = 9 + Math.floor(Math.random() * 18);
            cpuValue.textContent = `${nextValue}%`;
        }, 2400);
    }

    function init() {
        bindEvents();
        renderHistory();
        updateConnectionMode();
        loadSettings();
        startTelemetry();
        setLiveTranscript('');
        setTimeout(updateConnectionMode, 700);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
