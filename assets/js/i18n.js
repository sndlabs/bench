// Internationalization support for SND-Bench
const translations = {
    en: {
        title: "SND-Bench Dashboard - LLM Benchmarking Platform",
        nav: {
            dashboard: "Dashboard",
            compare: "Compare Models",
            wandb: "W&B Project"
        },
        kpi: {
            totalBenchmarks: "Total Benchmarks",
            modelsTested: "Models Tested", 
            avgAccuracy: "Avg Accuracy",
            latestRun: "Latest Run",
            allTime: "All time",
            uniqueModels: "Unique models",
            acrossAllRuns: "Across all runs"
        },
        charts: {
            performanceOverTime: "Performance Over Time",
            modelDistribution: "Model Performance Distribution"
        },
        table: {
            recentRuns: "Recent Benchmark Runs",
            model: "Model",
            quantization: "Quantization",
            accuracy: "Accuracy",
            tasks: "Tasks",
            timestamp: "Timestamp",
            actions: "Actions",
            details: "Details",
            showing: "Showing",
            to: "to",
            of: "of",
            runs: "runs",
            previous: "Previous",
            next: "Next"
        },
        ai: {
            latestAnalysis: "Latest AI Analysis",
            loading: "Loading latest analysis..."
        },
        footer: {
            copyright: "SND-Bench © 2025"
        },
        tasks: {
            // Korean task names
            kobest_boolq: "Korean Boolean QA",
            kobest_copa: "Korean COPA",
            kobest_hellaswag: "Korean HellaSwag",
            kobest_sentineg: "Korean Sentiment",
            kobest_wic: "Korean WiC",
            kmmlu: "Korean MMLU",
            klue_nli: "Korean NLI",
            klue_sts: "Korean STS",
            klue_ynat: "Korean Topic Classification",
            nsmc: "Naver Sentiment",
            kohatespeech: "Korean Hate Speech"
        }
    },
    ko: {
        title: "SND-Bench 대시보드 - LLM 벤치마킹 플랫폼",
        nav: {
            dashboard: "대시보드",
            compare: "모델 비교",
            wandb: "W&B 프로젝트"
        },
        kpi: {
            totalBenchmarks: "전체 벤치마크",
            modelsTested: "테스트된 모델",
            avgAccuracy: "평균 정확도",
            latestRun: "최신 실행",
            allTime: "전체 기간",
            uniqueModels: "고유 모델",
            acrossAllRuns: "모든 실행에 걸쳐"
        },
        charts: {
            performanceOverTime: "시간별 성능 추이",
            modelDistribution: "모델 성능 분포"
        },
        table: {
            recentRuns: "최근 벤치마크 실행",
            model: "모델",
            quantization: "양자화",
            accuracy: "정확도",
            tasks: "태스크",
            timestamp: "시간",
            actions: "작업",
            details: "상세",
            showing: "표시 중",
            to: "~",
            of: "/",
            runs: "개 실행",
            previous: "이전",
            next: "다음"
        },
        ai: {
            latestAnalysis: "최신 AI 분석",
            loading: "최신 분석을 불러오는 중..."
        },
        footer: {
            copyright: "SND-Bench © 2025"
        },
        tasks: {
            // Korean task names in Korean
            kobest_boolq: "한국어 불린 질의응답",
            kobest_copa: "한국어 인과관계 추론",
            kobest_hellaswag: "한국어 상황 완성",
            kobest_sentineg: "한국어 감성 분석",
            kobest_wic: "한국어 단어 의미 구분",
            kmmlu: "한국어 MMLU",
            klue_nli: "한국어 자연어 추론",
            klue_sts: "한국어 문장 유사도",
            klue_ynat: "한국어 주제 분류",
            nsmc: "네이버 영화 감성분석",
            kohatespeech: "한국어 혐오 발언 탐지"
        }
    }
};

// Language management
class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('snd-bench-lang') || 'en';
        this.translations = translations;
    }

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('snd-bench-lang', lang);
            document.documentElement.lang = lang;
            this.updatePageContent();
        }
    }

    t(key) {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];
        
        for (const k of keys) {
            value = value?.[k];
        }
        
        return value || key;
    }

    updatePageContent() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.hasAttribute('data-i18n-attr')) {
                const attr = element.getAttribute('data-i18n-attr');
                element.setAttribute(attr, translation);
            } else {
                element.textContent = translation;
            }
        });

        // Update page title
        document.title = this.t('title');

        // Trigger custom event for dynamic content
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { language: this.currentLang } 
        }));
    }

    // Format task name with localization
    formatTaskName(taskName) {
        return this.t(`tasks.${taskName}`) || taskName;
    }

    // Check if current language is Korean
    isKorean() {
        return this.currentLang === 'ko';
    }
}

// Create global instance
window.i18n = new I18n();

// Add language switcher to page
function addLanguageSwitcher() {
    const nav = document.querySelector('nav .flex.items-center');
    if (!nav) return;

    const switcher = document.createElement('div');
    switcher.className = 'mr-4';
    switcher.innerHTML = `
        <select id="languageSwitcher" class="px-3 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="en" ${window.i18n.currentLang === 'en' ? 'selected' : ''}>English</option>
            <option value="ko" ${window.i18n.currentLang === 'ko' ? 'selected' : ''}>한국어</option>
        </select>
    `;

    nav.insertBefore(switcher, nav.firstChild);

    // Add event listener
    document.getElementById('languageSwitcher').addEventListener('change', (e) => {
        window.i18n.setLanguage(e.target.value);
    });
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        addLanguageSwitcher();
        window.i18n.updatePageContent();
    });
} else {
    addLanguageSwitcher();
    window.i18n.updatePageContent();
}