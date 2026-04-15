const state = {
    category: window.APP_CONFIG.defaultCategory,
    region: "",
    search: "",
    savedArticles: [],
    chartInstances: {},
    previousSnapshot: null,
    riskTrendHistory: [],
    heatMap: null,
    heatLayer: null,
    heatMarkers: [],
    latestArticles: []
};

const REGION_NAMES = [
    "India",
    "Taiwan",
    "Russia",
    "China",
    "Japan",
    "Israel",
    "Middle East",
    "Europe",
    "USA",
    "South America",
    "Africa",
    "Antarctica"
];

const REGION_COORDINATES = {
    India: [22.5, 78.9],
    Taiwan: [23.7, 121.0],
    Russia: [61.5, 105.3],
    China: [35.8, 104.1],
    Japan: [36.2, 138.2],
    Israel: [31.0, 35.0],
    "Middle East": [29.5, 45.0],
    Europe: [54.5, 15.0],
    USA: [39.8, -98.5],
    "South America": [-15.6, -58.0],
    Africa: [2.5, 20.0],
    Antarctica: [-82.8, 18.0]
};

const CATEGORY_NAMES = ["Geopolitics", "War", "Crime"];

const CHART_COLORS = {
    green: "#2F7D5C",
    amber: "#C38B2F",
    red: "#B13C3C",
    navy: "#17324D",
    slate: "#506678",
    steel: "#6D8797",
    ice: "#A9BDC8",
    sand: "#8F7A52",
    grid: "rgba(23, 50, 77, 0.12)"
};

const elements = {
    articlesGrid: document.getElementById("articlesGrid"),
    emptyState: document.getElementById("emptyState"),
    messageBox: document.getElementById("messageBox"),
    dailySummary: document.getElementById("dailySummary"),
    securityFocus: document.getElementById("securityFocus"),
    topStories: document.getElementById("topStories"),
    resultsCount: document.getElementById("resultsCount"),
    newsHeading: document.getElementById("newsHeading"),
    statusBadge: document.getElementById("statusBadge"),
    searchInput: document.getElementById("searchInput"),
    refreshButton: document.getElementById("refreshButton"),
    telegramButton: document.getElementById("telegramButton"),
    indiaFocus: document.getElementById("indiaFocus"),
    indiaImpactBadge: document.getElementById("indiaImpactBadge"),
    indiaImpactReasons: document.getElementById("indiaImpactReasons"),
    predictionTitle: document.getElementById("predictionTitle"),
    predictionSummary: document.getElementById("predictionSummary"),
    predictionTag: document.getElementById("predictionTag"),
    predictionNotes: document.getElementById("predictionNotes")
};

function showMessage(message, visible = true) {
    elements.messageBox.textContent = message;
    elements.messageBox.classList.toggle("hidden", !visible || !message);
}

function formatDate(value) {
    if (!value) return "Unknown date";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function showLoading() {
    elements.articlesGrid.innerHTML = `
        <div class="article-card skeleton"></div>
        <div class="article-card skeleton"></div>
        <div class="article-card skeleton"></div>
        <div class="article-card skeleton"></div>
    `;
}

function saveArticle(title) {
    if (!state.savedArticles.includes(title)) {
        state.savedArticles.push(title);
        alert("Article saved");
    }
}

function shareArticle(url) {
    navigator.clipboard.writeText(url);
    alert("Article link copied");
}

function renderTopStories(stories) {
    elements.topStories.innerHTML = "";

    if (!stories || stories.length === 0) {
        elements.topStories.innerHTML = "<div class='story-card'>No top stories yet</div>";
        return;
    }

    stories.forEach((story, index) => {
        const card = document.createElement("div");
        card.className = "story-card";
        card.innerHTML = `
            <strong>#${index + 1}</strong>
            <h3>${story.title}</h3>
            <p class="article-meta">${formatDate(story.published_at)}</p>
        `;
        elements.topStories.appendChild(card);
    });
}

function renderArticles(articles) {
    elements.articlesGrid.innerHTML = "";
    elements.resultsCount.textContent = `${articles.length} articles`;

    if (!articles || articles.length === 0) {
        elements.emptyState.classList.remove("hidden");
        return;
    }

    elements.emptyState.classList.add("hidden");

    articles.forEach((article) => {
        const card = document.createElement("article");
        card.className = "article-card";

        card.innerHTML = `
            <div class="risk-tag ${article.risk_level}">
                ${article.risk_level.toUpperCase()} RISK
            </div>
            <h3>${article.title}</h3>
            <p class="article-meta">${formatDate(article.published_at)}</p>
            <p class="article-description">${article.description || "No description available"}</p>
            <div class="article-actions">
                <button class="save-btn">Save</button>
                <button class="share-btn">Share</button>
            </div>
            <a class="article-link" href="${article.url}" target="_blank" rel="noopener noreferrer">
                Read original article
            </a>
        `;

        card.querySelector(".save-btn").addEventListener("click", () => saveArticle(article.title));
        card.querySelector(".share-btn").addEventListener("click", () => shareArticle(article.url));
        elements.articlesGrid.appendChild(card);
    });
}

function updateAnalytics(articles, summary) {
    const metrics = summary.metrics || {};

    document.getElementById("metricArticles").textContent =
        metrics.articles_today ?? articles.length;
    document.getElementById("metricHighRisk").textContent =
        metrics.high_risk_count ?? articles.filter((article) => article.risk_level === "high").length;
    document.getElementById("metricSources").textContent = 0;
    document.getElementById("metricStrategic").textContent =
        metrics.strategic_count ?? articles.filter((article) => article.strategic_relevance).length;
    document.getElementById("metricIndiaImpact").textContent =
        metrics.india_impact_high ?? articles.filter((article) => article.india_impact_label === "high").length;
    document.getElementById("metricSourceGroups").textContent =
        new Set(articles.map((article) => article.source_group || "global_news")).size;
}

function updateTicker(articles) {
    const ticker = document.getElementById("breakingTicker");
    if (!ticker) return;

    const headlines = articles
        .slice(0, 5)
        .map((article) => `<span class="breaking-label">[Breaking]</span> ${article.title}`)
        .join("   |   ");

    ticker.innerHTML = headlines || "No breaking headlines available right now.";
}

function countBy(items, mapper) {
    return items.reduce((counts, item) => {
        const key = mapper(item);
        counts[key] = (counts[key] || 0) + 1;
        return counts;
    }, {});
}

function detectRegions(articles) {
    const counts = Object.fromEntries(REGION_NAMES.map((name) => [name, 0]));

    articles.forEach((article) => {
        const content = `${article.title || ""} ${article.description || ""}`.toLowerCase();
        REGION_NAMES.forEach((region) => {
            if (content.includes(region.toLowerCase())) {
                counts[region] += 1;
            }
        });
    });

    return counts;
}

function detectCategories(articles) {
    const counts = Object.fromEntries(CATEGORY_NAMES.map((name) => [name, 0]));

    articles.forEach((article) => {
        const content = `${article.title || ""} ${article.description || ""}`.toLowerCase();
        if (["sanction", "diplom", "alliance", "border", "naval"].some((term) => content.includes(term))) {
            counts.Geopolitics += 1;
        }
        if (["war", "military", "conflict", "strike", "ceasefire", "missile", "troops"].some((term) => content.includes(term))) {
            counts.War += 1;
        }
        if (["crime", "cartel", "gang", "trafficking", "homicide", "smuggling", "terror"].some((term) => content.includes(term))) {
            counts.Crime += 1;
        }
    });

    return counts;
}

function getIndiaImpactBreakdown(articles) {
    const counts = countBy(articles, (article) => article.india_impact_label || "low");
    return {
        low: counts.low || 0,
        medium: counts.medium || 0,
        high: counts.high || 0
    };
}

function getSourceGroupBreakdown(articles) {
    const normalized = articles.map((article) => {
        const group = (article.source_group || "global_news").toLowerCase();
        if (group === "india_news") return "India News";
        if (group === "india_think_tank") return "Think Tanks";
        return "Global News";
    });

    const counts = countBy(normalized, (group) => group);
    return {
        "Global News": counts["Global News"] || 0,
        "India News": counts["India News"] || 0,
        "Think Tanks": counts["Think Tanks"] || 0
    };
}

function updateRiskTrendHistory(articles) {
    const highRiskCount = articles.filter((article) => (article.risk_level || "").toLowerCase() === "high").length;
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    state.riskTrendHistory.push({ label: timestamp, value: highRiskCount });
    if (state.riskTrendHistory.length > 8) {
        state.riskTrendHistory.shift();
    }
}

function ensureCanvasBounds(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return null;

    canvas.style.width = "100%";
    canvas.style.height = "260px";
    canvas.width = canvas.clientWidth || 400;
    canvas.height = 260;
    return canvas;
}

function destroyChart(chartId) {
    if (state.chartInstances[chartId]) {
        state.chartInstances[chartId].destroy();
        delete state.chartInstances[chartId];
    }
}

function createOrUpdateChart(chartId, type, labels, values, color, options = {}) {
    const canvas = ensureCanvasBounds(chartId);
    if (!canvas || typeof Chart === "undefined") return;

    destroyChart(chartId);

    state.chartInstances[chartId] = new Chart(canvas, {
        type,
        data: {
            labels,
            datasets: [
                {
                    label: "Articles",
                    data: values,
                    backgroundColor: type === "line" ? "rgba(161, 58, 36, 0.15)" : color,
                    borderColor: type === "line" ? CHART_COLORS.red : Array.isArray(color) ? color : CHART_COLORS.navy,
                    borderWidth: type === "line" ? 3 : 1,
                    borderRadius: type === "bar" ? 10 : 0,
                    fill: type === "line",
                    tension: type === "line" ? 0.35 : 0,
                    pointRadius: type === "line" ? 4 : 0,
                    hoverOffset: type === "doughnut" ? 8 : 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 700,
                easing: "easeOutQuart"
            },
            plugins: {
                legend: {
                    display: type === "doughnut",
                    position: "bottom",
                    labels: {
                        color: CHART_COLORS.navy,
                        usePointStyle: true,
                        boxWidth: 10
                    }
                }
            },
            scales: type === "doughnut"
                ? {}
                : {
                    x: {
                        beginAtZero: !options.indexAxis || options.indexAxis === "y",
                        grid: {
                            color: CHART_COLORS.grid,
                            display: options.indexAxis === "y"
                        },
                        ticks: {
                            color: CHART_COLORS.navy,
                            precision: 0
                        }
                    },
                    y: {
                        beginAtZero: options.indexAxis !== "y",
                        grid: {
                            color: CHART_COLORS.grid,
                            display: options.indexAxis !== "y"
                        },
                        ticks: {
                            color: CHART_COLORS.navy,
                            precision: 0
                        }
                    }
                },
            ...options
        }
    });
}

function initializeHeatMap() {
    const mapContainer = document.getElementById("conflictHeatMap");
    if (!mapContainer || typeof L === "undefined") return;

    if (!state.heatMap) {
        state.heatMap = L.map("conflictHeatMap", {
            zoomControl: false,
            attributionControl: false,
            worldCopyJump: true
        }).setView([25, 18], 2);

        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
            subdomains: "abcd",
            maxZoom: 6
        }).addTo(state.heatMap);
    }
}

function updateHeatMap(regionCounts) {
    if (document.getElementById("visualizationsView").classList.contains("hidden")) {
        return;
    }

    initializeHeatMap();
    if (!state.heatMap || typeof L === "undefined") return;

    const points = Object.entries(regionCounts)
        .filter(([, count]) => count > 0)
        .map(([region, count]) => {
            const coords = REGION_COORDINATES[region];
            if (!coords) return null;
            return [coords[0], coords[1], Math.min(1, count / 6 + 0.2)];
        })
        .filter(Boolean);

    if (state.heatLayer) {
        state.heatMap.removeLayer(state.heatLayer);
    }

    state.heatMarkers.forEach((marker) => state.heatMap.removeLayer(marker));
    state.heatMarkers = [];

    state.heatLayer = L.heatLayer(points.length ? points : [[20, 0, 0.05]], {
        radius: 30,
        blur: 24,
        maxZoom: 4,
        gradient: {
            0.2: "#2f7d5c",
            0.45: "#c38b2f",
            0.75: "#b13c3c",
            1.0: "#ff5c5c"
        }
    }).addTo(state.heatMap);

    Object.entries(regionCounts)
        .filter(([, count]) => count > 0)
        .forEach(([region, count]) => {
            const coords = REGION_COORDINATES[region];
            if (!coords) return;

            const marker = L.circleMarker(coords, {
                radius: Math.min(16, 6 + count),
                color: "#f4efe7",
                weight: 1,
                fillColor: count >= 5 ? "#b13c3c" : count >= 3 ? "#c38b2f" : "#2f7d5c",
                fillOpacity: 0.75
            }).bindTooltip(`${region}: ${count}`, {
                permanent: false,
                direction: "top",
                className: "heatmap-tooltip"
            });

            marker.addTo(state.heatMap);
            state.heatMarkers.push(marker);
        });

    setTimeout(() => {
        state.heatMap.invalidateSize();
    }, 100);
}

function updateCharts(articles) {
    const riskCounts = countBy(articles, (article) => article.risk_level || "low");
    const regionCounts = detectRegions(articles);
    const categoryCounts = detectCategories(articles);
    const indiaImpactCounts = getIndiaImpactBreakdown(articles);
    const sourceGroupCounts = getSourceGroupBreakdown(articles);

    updateRiskTrendHistory(articles);

    createOrUpdateChart(
        "riskChart",
        "doughnut",
        ["Low", "Medium", "High"],
        [riskCounts.low || 0, riskCounts.medium || 0, riskCounts.high || 0],
        [CHART_COLORS.green, CHART_COLORS.amber, CHART_COLORS.red]
    );

    const topRegions = Object.entries(regionCounts)
        .filter((entry) => entry[1] > 0)
        .sort((left, right) => right[1] - left[1])
        .slice(0, 6);

    createOrUpdateChart(
        "regionChart",
        "bar",
        topRegions.map((entry) => entry[0]),
        topRegions.map((entry) => entry[1]),
        [CHART_COLORS.navy, CHART_COLORS.slate, CHART_COLORS.steel, CHART_COLORS.ice, CHART_COLORS.sand, CHART_COLORS.amber],
        { indexAxis: "y" }
    );

    createOrUpdateChart(
        "categoryChart",
        "bar",
        Object.keys(categoryCounts),
        Object.values(categoryCounts),
        [CHART_COLORS.navy, CHART_COLORS.red, CHART_COLORS.amber]
    );

    createOrUpdateChart(
        "indiaImpactChart",
        "doughnut",
        ["Low", "Medium", "High"],
        [indiaImpactCounts.low, indiaImpactCounts.medium, indiaImpactCounts.high],
        [CHART_COLORS.green, CHART_COLORS.amber, CHART_COLORS.red]
    );

    createOrUpdateChart(
        "sourceGroupChart",
        "bar",
        ["Global News", "India News", "Think Tanks"],
        [
            sourceGroupCounts["Global News"],
            sourceGroupCounts["India News"],
            sourceGroupCounts["Think Tanks"]
        ],
        [CHART_COLORS.navy, CHART_COLORS.steel, CHART_COLORS.sand]
    );

    createOrUpdateChart(
        "riskTrendChart",
        "line",
        state.riskTrendHistory.map((item) => item.label),
        state.riskTrendHistory.map((item) => item.value),
        CHART_COLORS.red
    );

    updateHeatMap(regionCounts);
}

function buildPrediction(articles) {
    const highRiskCount = articles.filter((article) => article.risk_level === "high").length;
    const strategicCount = articles.filter((article) => article.strategic_relevance).length;
    const indiaImpactHigh = articles.filter((article) => article.india_impact_label === "high").length;
    const warSignals = articles.filter((article) => {
        const content = `${article.title || ""} ${article.description || ""}`.toLowerCase();
        return ["war", "missile", "strike", "military", "troops", "attack"].some((term) => content.includes(term));
    }).length;
    const diplomacySignals = articles.filter((article) => {
        const content = `${article.title || ""} ${article.description || ""}`.toLowerCase();
        return ["ceasefire", "talks", "meeting", "diplomacy", "summit", "agreement"].some((term) => content.includes(term));
    }).length;

    const previous = state.previousSnapshot || { total: 0, highRisk: 0 };
    const totalChange = articles.length - previous.total;
    const highRiskChange = highRiskCount - previous.highRisk;

    let title = "Stable outlook";
    let tag = "neutral";
    let summary = "The current headlines suggest a mixed but manageable security picture.";

    if (highRiskCount >= 6 || warSignals >= 8 || highRiskChange >= 3 || indiaImpactHigh >= 4) {
        title = "Rising risk";
        tag = "high";
        summary = "High-risk, conflict-linked, or India-sensitive headlines are clustering, suggesting a hotter near-term environment.";
    } else if (diplomacySignals > warSignals && highRiskCount <= 2 && indiaImpactHigh <= 1) {
        title = "Cooling down";
        tag = "low";
        summary = "Diplomatic and de-escalation language is stronger than conflict signals in the latest flow.";
    }

    const notes = [
        `${highRiskCount} high-risk stories are present in the current view.`,
        `${strategicCount} stories are marked strategically relevant.`,
        `${indiaImpactHigh} stories currently have high potential impact on India.`,
        `${warSignals} stories contain direct conflict or military signals.`,
        `${diplomacySignals} stories contain diplomacy or de-escalation signals.`,
        totalChange > 0
            ? `Article volume is up by ${totalChange} compared with the previous refresh.`
            : totalChange < 0
                ? `Article volume is down by ${Math.abs(totalChange)} compared with the previous refresh.`
                : "Article volume is unchanged versus the previous refresh.",
        highRiskChange > 0
            ? `High-risk story count increased by ${highRiskChange}.`
            : highRiskChange < 0
                ? `High-risk story count decreased by ${Math.abs(highRiskChange)}.`
                : "High-risk story count is unchanged."
    ];

    elements.predictionTitle.textContent = title;
    elements.predictionSummary.textContent = summary;
    elements.predictionTag.textContent = tag === "high" ? "Escalation watch" : tag === "low" ? "Cooling signal" : "Balanced signal";
    elements.predictionTag.className = `prediction-tag ${tag}`;
    elements.predictionNotes.innerHTML = notes.map((note) => `<div class="prediction-note">${note}</div>`).join("");

    state.previousSnapshot = {
        total: articles.length,
        highRisk: highRiskCount
    };
}

function updateIndiaImpactPanel(summary, articles) {
    elements.indiaFocus.textContent = summary.india_focus || "No India impact focus available yet.";

    const highImpactArticles = articles
        .filter((article) => article.india_impact_score >= 4)
        .sort((left, right) => right.india_impact_score - left.india_impact_score)
        .slice(0, 4);

    const avgImpact = summary.metrics?.avg_india_impact ?? 0;
    elements.indiaImpactBadge.textContent =
        avgImpact >= 5 ? "Elevated India-linked pressure"
        : avgImpact >= 3 ? "Moderate India-linked pressure"
        : "Low India-linked pressure";

    if (highImpactArticles.length === 0) {
        elements.indiaImpactReasons.innerHTML = "<div class='prediction-note'>No strong India-linked signals in the current filtered view yet.</div>";
        return;
    }

    elements.indiaImpactReasons.innerHTML = highImpactArticles.map((article) => {
        const reasons = (article.india_impact_reasons || []).join(", ") || "general strategic linkage";
        return `
            <div class="prediction-note">
                <strong>${article.india_impact_label.toUpperCase()} impact</strong>
                <p>${article.title}</p>
                <p>Score: ${article.india_impact_score} | Reasons: ${reasons}</p>
            </div>
        `;
    }).join("");
}

function updateVisualizations(articles) {
    state.latestArticles = articles;
    updateCharts(articles);
    buildPrediction(articles);
}

function resizeVisualizations() {
    Object.values(state.chartInstances).forEach((chart) => chart.resize());
    if (state.heatMap) {
        setTimeout(() => state.heatMap.invalidateSize(), 100);
    }
}

function activateView(viewName) {
    document.querySelectorAll(".nav-tab").forEach((button) => {
        button.classList.toggle("active", button.dataset.view === viewName);
    });

    document.getElementById("dashboardView").classList.toggle("hidden", viewName !== "dashboard");
    document.getElementById("visualizationsView").classList.toggle("hidden", viewName !== "visualizations");

    if (viewName === "visualizations") {
        setTimeout(() => {
            initializeHeatMap();
            updateCharts(state.latestArticles || []);
            resizeVisualizations();
        }, 180);
    }
}

async function loadNews() {
    const params = new URLSearchParams({
        category: state.category,
        region: state.region,
        search: state.search
    });

    elements.statusBadge.textContent = "Loading...";
    showLoading();

    try {
        const response = await fetch(`/api/news?${params.toString()}`);
        const data = await response.json();

        if (data.error) {
            showMessage(data.error, true);
        } else {
            showMessage("", false);
        }

        elements.newsHeading.textContent = `${state.category} Headlines`;
        elements.dailySummary.textContent = data.summary.summary_text;
        elements.securityFocus.textContent = data.summary.security_focus;
        elements.statusBadge.textContent = data.telegram_configured
            ? "Telegram connected"
            : "Telegram not configured";

        renderTopStories(data.summary.top_stories);
        renderArticles(data.articles);
        updateAnalytics(data.articles, data.summary);
        updateTicker(data.articles);
        updateIndiaImpactPanel(data.summary, data.articles);
        updateVisualizations(data.articles);
    } catch (error) {
        showMessage("Failed loading news", true);
        elements.statusBadge.textContent = "Error";
        renderArticles([]);
        updateAnalytics([], { metrics: {} });
        updateTicker([]);
        updateIndiaImpactPanel({ india_focus: "", metrics: {} }, []);
        updateVisualizations([]);
    }
}

async function refreshNews() {
    elements.statusBadge.textContent = "Refreshing...";

    try {
        const response = await fetch("/api/refresh", { method: "POST" });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || "Refresh failed");
        }

        showMessage(data.message, true);
        await loadNews();
    } catch (error) {
        showMessage("Refresh failed", true);
    }
}

async function sendTelegram() {
    elements.statusBadge.textContent = "Sending...";

    try {
        const response = await fetch("/api/send-telegram", { method: "POST" });
        const data = await response.json();
        showMessage(data.message, true);
    } catch (error) {
        showMessage("Telegram failed", true);
    }
}

let searchTimeout;

elements.searchInput.addEventListener("input", (event) => {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(async () => {
        state.search = event.target.value;
        await loadNews();
    }, 400);
});

document.querySelectorAll("[data-category]").forEach((button) => {
    button.addEventListener("click", async () => {
        document.querySelectorAll("[data-category]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        state.category = button.dataset.category;
        await loadNews();
    });
});

document.querySelectorAll("[data-region]").forEach((button) => {
    button.addEventListener("click", async () => {
        document.querySelectorAll("[data-region]").forEach((item) => item.classList.remove("active"));
        button.classList.add("active");
        state.region = button.dataset.region;
        await loadNews();
    });
});

document.querySelectorAll(".nav-tab").forEach((button) => {
    button.addEventListener("click", () => {
        activateView(button.dataset.view);
    });
});

elements.refreshButton.addEventListener("click", refreshNews);
elements.telegramButton.addEventListener("click", sendTelegram);
window.addEventListener("resize", resizeVisualizations);

loadNews();
setInterval(() => {
    refreshNews();
}, 300000);
