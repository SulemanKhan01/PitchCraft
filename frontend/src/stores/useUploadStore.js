import { create } from 'zustand'

const useUploadStore = create((set) => ({
  selectedFile: null,
  isUploading: false,
  status: null,
  isDragOver: false,

  setSelectedFile: (selectedFile) => set({ selectedFile }),

  setIsUploading: (isUploading) => set({ isUploading }),

  setStatus: (status) => set({ status }),

  setIsDragOver: (isDragOver) => set({ isDragOver }),

  resetUpload: () =>
    set({
      selectedFile: null,
      isUploading: false,
      status: null,
      isDragOver: false,
    }),
}))

export default useUploadStore
