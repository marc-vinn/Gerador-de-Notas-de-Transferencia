/**
 * Global Configuration and Storage Keys
 * Universal, clean, and dynamic naming.
 */
export const CONFIG = {
  STORAGE_KEYS: {
    EMITTER: "nfe_transfer_emitter_v1",
    RECIPIENT: "nfe_transfer_recipient_v1",
    PRODUCTS: "nfe_transfer_products_v1",
    FILENAME: "nfe_transfer_filename_v1",
    BOOKMARK: "nfe_transfer_bookmark_v1",
    MULTI_ANALYSIS_CACHE: "nfe_transfer_multi_analysis_v1"
  },
  MAX_FILE_SIZE_BYTES: 10 * 1024 * 1024, // 10MB
  SUPPORTED_EXTENSIONS: ["xls", "xlsx"],
  ENDPOINTS: {
    UPLOAD: "/api/upload",
    ANALYZE_MULTI: "/api/analyze-multi",
    GENERATE_XML: "/api/generate-xml"
  }
};
