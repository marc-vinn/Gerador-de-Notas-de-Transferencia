/**
 * Storage Manager Service
 * Manages LocalStorage persistence and secure session purging.
 */
import { CONFIG } from "../config.js";

export const StorageManager = {
  getEmitter() {
    try {
      const stored = localStorage.getItem(CONFIG.STORAGE_KEYS.EMITTER);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.warn("Error reading emitter storage:", e);
      return null;
    }
  },

  saveEmitter(data) {
    try {
      localStorage.setItem(CONFIG.STORAGE_KEYS.EMITTER, JSON.stringify(data));
    } catch (e) {
      console.warn("Error saving emitter storage:", e);
    }
  },

  clearEmitter() {
    try {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.EMITTER);
    } catch (e) {
      console.warn("Error clearing emitter storage:", e);
    }
  },

  getRecipient() {
    try {
      const stored = localStorage.getItem(CONFIG.STORAGE_KEYS.RECIPIENT);
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.warn("Error reading recipient storage:", e);
      return null;
    }
  },

  saveRecipient(data) {
    try {
      localStorage.setItem(CONFIG.STORAGE_KEYS.RECIPIENT, JSON.stringify(data));
    } catch (e) {
      console.warn("Error saving recipient storage:", e);
    }
  },

  clearRecipient() {
    try {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.RECIPIENT);
    } catch (e) {
      console.warn("Error clearing recipient storage:", e);
    }
  },

  getCachedProducts() {
    try {
      const p = localStorage.getItem(CONFIG.STORAGE_KEYS.PRODUCTS);
      const f = localStorage.getItem(CONFIG.STORAGE_KEYS.FILENAME);
      if (p && f) {
        return { filename: f, products: JSON.parse(p) };
      }
    } catch (e) {
      console.warn("Error reading product cache:", e);
    }
    return null;
  },

  saveCachedProducts(products, filename) {
    try {
      if (products && products.length > 0) {
        localStorage.setItem(CONFIG.STORAGE_KEYS.PRODUCTS, JSON.stringify(products));
        localStorage.setItem(CONFIG.STORAGE_KEYS.FILENAME, filename || "relatorio.xls");
      } else {
        this.clearCachedProducts();
      }
    } catch (e) {
      console.warn("Error saving product cache:", e);
    }
  },

  clearCachedProducts() {
    try {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.PRODUCTS);
      localStorage.removeItem(CONFIG.STORAGE_KEYS.FILENAME);
    } catch (e) {
      console.warn("Error clearing product cache:", e);
    }
  },

  getBookmarks() {
    try {
      const stored = localStorage.getItem(CONFIG.STORAGE_KEYS.BOOKMARK);
      return stored ? JSON.parse(stored) : [];
    } catch (e) {
      return [];
    }
  },

  saveBookmarks(codes) {
    try {
      localStorage.setItem(CONFIG.STORAGE_KEYS.BOOKMARK, JSON.stringify(codes));
    } catch (e) {
      console.warn("Error saving bookmarks:", e);
    }
  },

  clearBookmarks() {
    try {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.BOOKMARK);
    } catch (e) {
      console.warn("Error clearing bookmarks:", e);
    }
  },

  /**
   * Purgar dados de sessão e cache do navegador.
   * Por padrão preserva o cadastro da Matriz para conveniência do operador,
   * a menos que purgeEmitter seja explicitamente true.
   */
  purgeAllSessionData(purgeEmitter = false) {
    this.clearCachedProducts();
    this.clearBookmarks();
    this.clearRecipient();
    if (purgeEmitter) {
      this.clearEmitter();
    }
  }
};
