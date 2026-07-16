import { create } from 'zustand'

const useCoverLetterStore = create((set) => ({
  jdText: '',
  generatedContent: '',
  isGenerating: false,
  isDownloading: false,
  chunksUsed: 0,
  error: null,

  setJdText: (jdText) => set({ jdText, error: null }),

  setGeneratedContent: (generatedContent) => set({ generatedContent }),

  setIsGenerating: (isGenerating) => set({ isGenerating }),

  setIsDownloading: (isDownloading) => set({ isDownloading }),

  setChunksUsed: (chunksUsed) => set({ chunksUsed }),

  setError: (error) => set({ error }),

  resetCoverLetter: () =>
    set({
      jdText: '',
      generatedContent: '',
      isGenerating: false,
      isDownloading: false,
      chunksUsed: 0,
      error: null,
    }),
}))

export default useCoverLetterStore
