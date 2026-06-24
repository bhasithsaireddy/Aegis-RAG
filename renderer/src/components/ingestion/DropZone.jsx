import { useCallback } from 'react'
import { Upload, FileText, Image, Mic, File } from 'lucide-react'
import useStore from '../../store/store'

/**
 * DropZone - Drag-and-drop file upload area
 * Supports PDF, DOCX, images, and audio files
 */
export default function DropZone() {
    const { addToIngestionQueue } = useStore()

    const supportedFormats = [
        { ext: 'PDF', icon: FileText, color: 'text-red-400' },
        { ext: 'DOCX', icon: FileText, color: 'text-blue-400' },
        { ext: 'PNG/JPG', icon: Image, color: 'text-aegis-rag-text-secondary' },
        { ext: 'WAV/MP3', icon: Mic, color: 'text-purple-400' },
    ]

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
    }, [])

    const handleDragEnter = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        e.currentTarget.classList.add('dropzone-active')
    }, [])

    const handleDragLeave = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        e.currentTarget.classList.remove('dropzone-active')
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        e.currentTarget.classList.remove('dropzone-active')

        const files = Array.from(e.dataTransfer.files)
        if (files.length > 0) {
            const validFiles = files.filter(file => {
                const ext = file.name.split('.').pop()?.toLowerCase()
                return ['pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'wav', 'mp3'].includes(ext)
            })

            if (validFiles.length > 0) {
                addToIngestionQueue(validFiles)
            }
        }
    }, [addToIngestionQueue])

    const handleFileSelect = useCallback((e) => {
        const files = Array.from(e.target.files || [])
        if (files.length > 0) {
            addToIngestionQueue(files)
        }
        // Reset input
        e.target.value = ''
    }, [addToIngestionQueue])

    return (
        <div
            className="dropzone p-8 flex flex-col items-center justify-center min-h-[280px] cursor-pointer"
            onDragOver={handleDragOver}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
        >
            {/* Hidden File Input */}
            <input
                id="file-input"
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.png,.jpg,.jpeg,.wav,.mp3"
                onChange={handleFileSelect}
                className="hidden"
            />

            {/* Upload Icon */}
            <div className="w-20 h-20 rounded-3xl bg-aegis-rag-accent/10 flex items-center justify-center mb-6">
                <Upload size={36} className="text-aegis-rag-accent" />
            </div>

            {/* Text */}
            <h3 className="text-xl font-semibold text-aegis-rag-text-primary mb-2">
                Drop files here
            </h3>
            <p className="text-aegis-rag-text-secondary mb-6">
                or <span className="text-aegis-rag-accent cursor-pointer hover:underline">browse</span> to upload
            </p>

            {/* Supported Formats */}
            <div className="flex flex-wrap justify-center gap-3">
                {supportedFormats.map((format) => {
                    const Icon = format.icon
                    return (
                        <div
                            key={format.ext}
                            className="flex items-center gap-2 px-3 py-1.5 bg-aegis-rag-bg-elevated rounded-full"
                        >
                            <Icon size={14} className={format.color} />
                            <span className="text-xs text-aegis-rag-text-muted font-medium">{format.ext}</span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
