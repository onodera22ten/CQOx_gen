/**
 * Dataset Management Page
 * 
 * データセット管理画面（一覧、アップロード、プレビュー）
 */
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, Trash2, Eye, Plus, FileText } from 'lucide-react';
import { datasetsAPI, Dataset } from '../api/v1/datasets';

const DatasetManagement: React.FC = () => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const queryClient = useQueryClient();

  // Fetch datasets
  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsAPI.list()
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: datasetsAPI.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
    }
  });

  const handleDelete = (datasetId: string) => {
    if (confirm('このデータセットを削除しますか？')) {
      deleteMutation.mutate(datasetId);
    }
  };

  if (isLoading) {
    return <div className="p-6">Loading datasets...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">データセット管理</h1>
        <button
          onClick={() => setIsUploadModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"
        >
          <Plus size={20} />
          新規アップロード
        </button>
      </div>

      {/* Datasets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {datasets?.map((dataset) => (
          <div key={dataset.id} className="border rounded-lg p-4 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <FileText className="text-blue-600" size={24} />
                <h3 className="font-semibold text-lg">{dataset.name}</h3>
              </div>
            </div>

            {dataset.description && (
              <p className="text-gray-600 text-sm mb-3">{dataset.description}</p>
            )}

            <div className="grid grid-cols-2 gap-2 text-sm mb-4">
              <div>
                <span className="text-gray-500">行数:</span>
                <span className="ml-2 font-medium">{dataset.row_count?.toLocaleString() || '-'}</span>
              </div>
              <div>
                <span className="text-gray-500">列数:</span>
                <span className="ml-2 font-medium">{dataset.column_count || '-'}</span>
              </div>
            </div>

            <div className="text-xs text-gray-500 mb-3">
              作成日: {new Date(dataset.created_at).toLocaleDateString('ja-JP')}
            </div>

            <div className="flex gap-2">
              <button
                onClick={() => setSelectedDataset(dataset)}
                className="flex-1 bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded flex items-center justify-center gap-2"
              >
                <Eye size={16} />
                プレビュー
              </button>
              <button
                onClick={() => handleDelete(dataset.id)}
                className="bg-red-50 hover:bg-red-100 text-red-600 px-3 py-2 rounded flex items-center justify-center"
              >
                <Trash2 size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {datasets?.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <FileText size={48} className="mx-auto mb-4 text-gray-300" />
          <p>データセットがありません</p>
          <p className="text-sm mt-2">「新規アップロード」からデータセットを追加してください</p>
        </div>
      )}

      {/* Upload Modal */}
      {isUploadModalOpen && (
        <UploadModal onClose={() => setIsUploadModalOpen(false)} />
      )}

      {/* Preview Modal */}
      {selectedDataset && (
        <PreviewModal dataset={selectedDataset} onClose={() => setSelectedDataset(null)} />
      )}
    </div>
  );
};

// Upload Modal Component
const UploadModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [_uploadProgress, _setUploadProgress] = useState(0);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (data: { name: string; description: string; file: File }) => {
      const formData = new FormData();
      formData.append('file', data.file);
      formData.append('name', data.name);
      formData.append('description', data.description);

      const response = await fetch('/api/v1/upload/dataset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      });

      if (!response.ok) {
        const rawText = await response.text();
        if (response.status === 413) {
          throw new Error('ファイルサイズがサーバの許容上限を超えています。300MB 以下のファイルに分割するか、圧縮して再度お試しください。');
        }
        try {
          const errorJson = JSON.parse(rawText);
          throw new Error(errorJson.detail || errorJson.message || 'アップロードに失敗しました');
        } catch {
          const trimmed = rawText?.trim();
          throw new Error(trimmed ? `アップロードに失敗しました: ${trimmed.slice(0, 200)}` : 'アップロードに失敗しました');
        }
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      onClose();
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!name) {
        // ファイル名からデータセット名を自動設定
        setName(selectedFile.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('ファイルを選択してください');
      return;
    }
    uploadMutation.mutate({ name, description, file });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h2 className="text-2xl font-bold mb-4">新規データセット</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">データファイル</label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                accept=".csv,.json,.xlsx,.xls,.parquet,.pq"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                required
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="mx-auto mb-2 text-gray-400" size={32} />
                {file ? (
                  <p className="text-sm font-medium text-blue-600">{file.name}</p>
                ) : (
                  <>
                    <p className="text-sm text-gray-600">クリックしてファイルを選択</p>
                    <p className="text-xs text-gray-400 mt-1">対応形式: CSV, JSON, Excel (.xlsx/.xls), Parquet</p>
                    <p className="text-xs text-gray-400">最大300MB まで対応</p>
                  </>
                )}
              </label>
            </div>
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">データセット名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border rounded px-3 py-2 text-gray-900"
              placeholder="例: marketing_campaign_data"
              required
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">説明 (任意)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full border rounded px-3 py-2 text-gray-900"
              placeholder="例: 2024年Q1のマーケティングキャンペーンデータ"
              rows={3}
            />
          </div>

          {uploadMutation.isError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
              {uploadMutation.error?.message || 'アップロードに失敗しました'}
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              disabled={uploadMutation.isPending}
              className="px-4 py-2 border rounded hover:bg-gray-100 disabled:opacity-50"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={uploadMutation.isPending || !file}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              {uploadMutation.isPending ? (
                <>
                  <span className="animate-spin">⏳</span>
                  アップロード中...
                </>
              ) : (
                <>
                  <Upload size={16} />
                  アップロード
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Preview Modal Component
const PreviewModal: React.FC<{ dataset: Dataset; onClose: () => void }> = ({ dataset, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-auto">
        <h2 className="text-2xl font-bold mb-4">{dataset.name}</h2>
        <div className="mb-4">
          <p className="text-gray-600">{dataset.description}</p>
          <p className="text-sm text-gray-500 mt-2">
            {dataset.row_count?.toLocaleString()} 行 × {dataset.column_count} 列
          </p>
        </div>
        {/* TODO: データプレビューテーブル実装 */}
        <div className="border rounded p-4 bg-gray-50">
          <p className="text-gray-500">データプレビュー機能は近日実装予定</p>
        </div>
        <div className="mt-4 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            閉じる
          </button>
        </div>
      </div>
    </div>
  );
};

export default DatasetManagement;
