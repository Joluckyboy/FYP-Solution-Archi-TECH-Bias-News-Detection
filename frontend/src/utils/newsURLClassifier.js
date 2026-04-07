const NON_NEWS_DOMAINS = new Set([
  // Social media
  "facebook.com", "twitter.com", "x.com", "instagram.com",
  "tiktok.com", "snapchat.com", "pinterest.com", "linkedin.com",
  "reddit.com", "discord.com", "threads.net",
  // Streaming / entertainment
  "netflix.com", "twitch.tv", "spotify.com", "disneyplus.com",
  "hulu.com", "vimeo.com", "primevideo.com",
  // E-commerce
  "amazon.com", "ebay.com", "shopee.sg", "lazada.sg",
  "aliexpress.com", "etsy.com", "temu.com", "qoo10.sg",
  // Dev / tools
  "github.com", "stackoverflow.com", "notion.so",
  "figma.com", "canva.com", "slack.com", "zoom.us",
  // Search / AI
  "google.com", "bing.com", "duckduckgo.com",
  "openai.com", "anthropic.com", "claude.ai",
  // Reference
  "wikipedia.org", "medium.com", "quora.com", "imdb.com",
]);

export const isNonNewsDomain = (url) => {
  try {
    const hostname = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    return NON_NEWS_DOMAINS.has(hostname) ||
      [...NON_NEWS_DOMAINS].some(d => hostname.endsWith("." + d));
  } catch {
    return false;
  }
};

export const isYouTubeUrl = (url) => {
  try {
    const hostname = new URL(url).hostname.toLowerCase().replace(/^www\./, "");
    return hostname === "youtube.com" || hostname === "youtu.be";
  } catch {
    return false;
  }
};