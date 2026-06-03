import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { Upload, Film, CheckCircle, Loader2, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '@/components/DashboardLayout';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const UploadPage = () => {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedMovie, setUploadedMovie] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [languages, setLanguages] = useState([]);
  const [creatingJob, setCreatingJob] = useState(false);

  React.useEffect(() => {
    fetchLanguages();
  }, []);

  const fetchLanguages = async () => {
    try {
      const response = await axios.get(`${API}/languages`);
      setLanguages(response.data);
    } catch (error) {
      console.error('Error fetching languages:', error);
    }
  };

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const allowedFormats = ['mp4', 'mkv', 'avi'];
    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!allowedFormats.includes(fileExt)) {
      toast.error(`Format not supported. Allowed: ${allowedFormats.join(', ')}`);
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/movies/upload`, formData, {
        withCredentials: true,
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });

      setUploadedMovie(response.data);
      toast.success('Movie uploaded successfully!');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'video/mp4': ['.mp4'],
      'video/x-matroska': ['.mkv'],
      'video/x-msvideo': ['.avi'],
    },
    maxFiles: 1,
    disabled: uploading || uploadedMovie !== null,
  });

  const handleStartDubbing = async () => {
    if (!selectedLanguage) {
      toast.error('Please select a target language');
      return;
    }

    setCreatingJob(true);
    try {
      const response = await axios.post(
        `${API}/dubbing/create`,
        {
          movie_id: uploadedMovie.movie_id,
          target_language: selectedLanguage,
        },
        { withCredentials: true }
      );

      toast.success('Dubbing job started!');
      navigate(`/jobs`);
    } catch (error) {
      console.error('Error creating job:', error);
      toast.error(error.response?.data?.detail || 'Failed to start dubbing');
    } finally {
      setCreatingJob(false);
    }
  };

  const handleUploadAnother = () => {
    setUploadedMovie(null);
    setSelectedLanguage('');
    setUploadProgress(0);
  };

  return (
    <DashboardLayout>
      <div data-testid="upload-page-container" className="space-y-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-black tracking-tight mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Upload Movie
          </h1>
          <p className="text-zinc-400" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Upload your movie and dub it into any language
          </p>
        </div>

        {!uploadedMovie ? (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8"
          >
            <div
              {...getRootProps()}
              data-testid="dropzone-area"
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                isDragActive
                  ? 'border-purple-500 bg-purple-500/10'
                  : uploading
                  ? 'border-blue-500 bg-blue-500/10 cursor-not-allowed'
                  : 'border-white/20 hover:border-purple-500/50 hover:bg-white/5'
              }`}
            >
              <input {...getInputProps()} data-testid="file-input" />
              
              {uploading ? (
                <div className="space-y-4">
                  <Loader2 className="w-16 h-16 text-blue-500 mx-auto animate-spin" />
                  <p className="text-xl font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    Uploading... {uploadProgress}%
                  </p>
                  <div className="max-w-md mx-auto bg-zinc-800 rounded-full h-3 overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <Upload className="w-16 h-16 text-purple-500 mx-auto" />
                  <div>
                    <p className="text-xl font-semibold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                      {isDragActive ? 'Drop your movie here' : 'Drag & drop your movie here'}
                    </p>
                    <p className="text-zinc-500" style={{ fontFamily: 'Manrope, sans-serif' }}>
                      or click to browse
                    </p>
                  </div>
                  <p className="text-sm text-zinc-600" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    Supported formats: MP4, MKV, AVI
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <div className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
              <div className="flex items-start gap-4">
                <div className="bg-green-500/10 p-3 rounded-xl">
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    Movie Uploaded Successfully!
                  </h3>
                  <div className="space-y-1 text-sm" style={{ fontFamily: 'Manrope, sans-serif' }}>
                    <p className="text-zinc-300"><strong>Title:</strong> {uploadedMovie.title}</p>
                    <p className="text-zinc-300"><strong>Format:</strong> {uploadedMovie.format.toUpperCase()}</p>
                    <p className="text-zinc-300"><strong>Detected Language:</strong> {uploadedMovie.detected_language?.toUpperCase()}</p>
                    <p className="text-zinc-300"><strong>Size:</strong> {(uploadedMovie.file_size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-zinc-900/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
                <Globe className="w-5 h-5 text-purple-500" />
                Select Target Language
              </h3>
              <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                <SelectTrigger data-testid="language-selector" className="w-full bg-black/50 border-white/10 text-white">
                  <SelectValue placeholder="Choose a language" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10 text-white">
                  {languages.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code} className="hover:bg-white/10">
                      {lang.native_name} ({lang.name})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex gap-4">
              <button
                data-testid="start-dubbing-btn"
                onClick={handleStartDubbing}
                disabled={!selectedLanguage || creatingJob}
                className="flex-1 bg-[#E50914] hover:bg-[#c40812] disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-lg px-6 py-4 font-semibold shadow-[0_0_20px_rgba(229,9,20,0.4)] transition-all flex items-center justify-center gap-2"
              >
                {creatingJob ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Starting...
                  </>
                ) : (
                  <>
                    <Film className="w-5 h-5" />
                    Start AI Dubbing
                  </>
                )}
              </button>
              <button
                data-testid="upload-another-btn"
                onClick={handleUploadAnother}
                className="bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-lg px-6 py-4 font-medium backdrop-blur-md transition-all"
              >
                Upload Another
              </button>
            </div>
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  );
};
