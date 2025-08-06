import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  Eye, 
  Calendar, 
  User, 
  Tag, 
  Lock, 
  Shield,
  Clock,
  Hash,
  ExternalLink
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface DocumentMetadata {
  document_id: string;
  patient_id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  hash_sha256: string;
  document_type: string;
  document_category?: string;
  tags: string[];
  metadata: Record<string, any>;
  version: number;
  uploaded_by: string;
  uploaded_at: string;
  updated_at?: string;
  is_latest_version: boolean;
  auto_classification_confidence?: number;
}

interface DocumentViewerProps {
  document: DocumentMetadata;
  onDownload: (documentId: string) => Promise<void>;
  onViewVersions: (documentId: string) => void;
  isDownloading?: boolean;
}

export function DocumentViewer({ 
  document, 
  onDownload, 
  onViewVersions, 
  isDownloading = false 
}: DocumentViewerProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showMetadata, setShowMetadata] = useState(false);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getDocumentTypeColor = (type: string) => {
    const colors = {
      'LAB_RESULT': 'bg-blue-100 text-blue-800',
      'IMAGING': 'bg-purple-100 text-purple-800',
      'CLINICAL_NOTE': 'bg-green-100 text-green-800',
      'PRESCRIPTION': 'bg-orange-100 text-orange-800',
      'INSURANCE': 'bg-yellow-100 text-yellow-800',
      'DISCHARGE_SUMMARY': 'bg-red-100 text-red-800',
      'MEDICAL_RECORD': 'bg-indigo-100 text-indigo-800',
      'OTHER': 'bg-gray-100 text-gray-800'
    };
    return colors[type as keyof typeof colors] || colors.OTHER;
  };

  const canPreview = (mimeType: string) => {
    return mimeType.startsWith('image/') || mimeType === 'application/pdf';
  };

  const handlePreview = async () => {
    if (canPreview(document.mime_type)) {
      // In a real implementation, this would fetch the document content
      // For now, we'll show a placeholder
      setPreviewUrl(`/api/v1/documents/${document.document_id}/preview`);
    }
  };

  return (
    <div className="space-y-6">
      {/* Document Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-primary/10 rounded-lg">
                <FileText className="w-8 h-8 text-primary" />
              </div>
              <div className="flex-1">
                <CardTitle className="text-xl mb-2">{document.filename}</CardTitle>
                <CardDescription className="space-y-1">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {formatDate(document.uploaded_at)}
                    </span>
                    <span className="flex items-center gap-1">
                      <User className="w-4 h-4" />
                      User {document.uploaded_by.slice(0, 8)}
                    </span>
                    <span>{formatFileSize(document.file_size)}</span>
                  </div>
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              {canPreview(document.mime_type) && (
                <Button variant="outline" size="sm" onClick={handlePreview}>
                  <Eye className="w-4 h-4 mr-2" />
                  Preview
                </Button>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => onDownload(document.document_id)}
                disabled={isDownloading}
              >
                <Download className="w-4 h-4 mr-2" />
                {isDownloading ? 'Downloading...' : 'Download'}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2 mb-4">
            <Badge className={getDocumentTypeColor(document.document_type)}>
              {document.document_type.replace('_', ' ')}
            </Badge>
            {document.document_category && (
              <Badge variant="outline">{document.document_category}</Badge>
            )}
            {document.tags.map((tag) => (
              <Badge key={tag} variant="secondary">
                <Tag className="w-3 h-3 mr-1" />
                {tag}
              </Badge>
            ))}
            {!document.is_latest_version && (
              <Badge variant="destructive">Old Version</Badge>
            )}
          </div>

          {/* Quick Info Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="text-center">
              <div className="text-sm text-gray-500">Version</div>
              <div className="font-semibold">{document.version}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Type</div>
              <div className="font-semibold text-xs">{document.mime_type.split('/')[1]?.toUpperCase()}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Security</div>
              <div className="font-semibold flex items-center justify-center gap-1">
                <Shield className="w-3 h-3" />
                Encrypted
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Compliance</div>
              <div className="font-semibold flex items-center justify-center gap-1">
                <Lock className="w-3 h-3" />
                SOC2/HIPAA
              </div>
            </div>
          </div>

          {/* AI Classification Confidence */}
          {document.auto_classification_confidence && (
            <Alert className="mt-4">
              <Shield className="h-4 w-4" />
              <AlertDescription>
                <strong>AI Classification:</strong> Automatically classified with {
                  Math.round(document.auto_classification_confidence * 100)
                }% confidence as {document.document_type.replace('_', ' ')}.
              </AlertDescription>
            </Alert>
          )}

          {/* Actions */}
          <div className="flex gap-2 mt-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onViewVersions(document.document_id)}
            >
              <Clock className="w-4 h-4 mr-2" />
              Version History
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowMetadata(!showMetadata)}
            >
              <Hash className="w-4 h-4 mr-2" />
              {showMetadata ? 'Hide' : 'Show'} Metadata
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document Preview */}
      {previewUrl && (
        <Card>
          <CardHeader>
            <CardTitle>Document Preview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg p-4 bg-gray-50 min-h-[400px] flex items-center justify-center">
              {document.mime_type.startsWith('image/') ? (
                <img 
                  src={previewUrl} 
                  alt={document.filename}
                  className="max-w-full max-h-96 object-contain"
                />
              ) : document.mime_type === 'application/pdf' ? (
                <iframe
                  src={previewUrl}
                  className="w-full h-96 border-0"
                  title={document.filename}
                />
              ) : (
                <div className="text-center text-gray-500">
                  <FileText className="w-16 h-16 mx-auto mb-4" />
                  <p>Preview not available for this file type</p>
                  <Button variant="link" onClick={() => onDownload(document.document_id)}>
                    <ExternalLink className="w-4 h-4 mr-2" />
                    Download to view
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Extended Metadata */}
      {showMetadata && (
        <Card>
          <CardHeader>
            <CardTitle>Document Metadata</CardTitle>
            <CardDescription>
              Detailed information about this document
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Identifiers */}
              <div className="space-y-3">
                <h4 className="font-semibold text-sm text-gray-700">Identifiers</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Document ID:</span>
                    <span className="font-mono text-xs">{document.document_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Patient ID:</span>
                    <span className="font-mono text-xs">{document.patient_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">SHA256 Hash:</span>
                    <span className="font-mono text-xs">{document.hash_sha256.slice(0, 16)}...</span>
                  </div>
                </div>
              </div>

              {/* Timestamps */}
              <div className="space-y-3">
                <h4 className="font-semibold text-sm text-gray-700">Timestamps</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Uploaded:</span>
                    <span>{formatDate(document.uploaded_at)}</span>
                  </div>
                  {document.updated_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Updated:</span>
                      <span>{formatDate(document.updated_at)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Custom Metadata */}
              {Object.keys(document.metadata).length > 0 && (
                <div className="md:col-span-2 space-y-3">
                  <h4 className="font-semibold text-sm text-gray-700">Custom Metadata</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    {Object.entries(document.metadata).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-gray-500 capitalize">{key.replace('_', ' ')}:</span>
                        <span className="text-right max-w-[200px] truncate">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default DocumentViewer;