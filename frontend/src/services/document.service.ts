// ============================================
// DOCUMENT MANAGEMENT SERVICE
// ============================================

import { apiClient } from './api';

// Document Types
export type DocumentType = 
  | 'LAB_RESULT'
  | 'IMAGING'
  | 'CLINICAL_NOTE'
  | 'PRESCRIPTION'
  | 'DISCHARGE_SUMMARY'
  | 'OPERATIVE_REPORT'
  | 'PATHOLOGY_REPORT'
  | 'RADIOLOGY_REPORT'
  | 'CONSULTATION_NOTE'
  | 'PROGRESS_NOTE'
  | 'MEDICATION_LIST'
  | 'ALLERGY_LIST'
  | 'VITAL_SIGNS'
  | 'INSURANCE_CARD'
  | 'IDENTIFICATION_DOCUMENT'
  | 'CONSENT_FORM'
  | 'REFERRAL'
  | 'OTHER';

// Interfaces
export interface DocumentMetadata {
  document_id: string;
  patient_id: string;
  filename: string;
  storage_key: string;
  file_size: number;
  mime_type: string;
  hash_sha256: string;
  document_type: DocumentType;
  document_category?: string;
  auto_classification_confidence?: number;
  extracted_text?: string;
  tags: string[];
  metadata: Record<string, any>;
  version: number;
  parent_document_id?: string;
  is_latest_version: boolean;
  uploaded_by: string;
  uploaded_at: string;
  updated_at?: string;
  updated_by?: string;
}

export interface ClassificationResult {
  document_type: string;
  confidence: number;
  category: string;
  subcategory?: string;
  tags: string[];
  classification_method: string;
  processing_time_ms: number;
  metadata: Record<string, any>;
}

export interface VersionInfo {
  version_id: string;
  version_number: number;
  version_type: string;
  created_at: string;
  created_by: string;
  change_summary: string;
  is_current: boolean;
  file_size: number;
  tags: string[];
}

export interface DocumentSearchParams {
  patient_id?: string;
  document_types?: DocumentType[];
  document_category?: string;
  tags?: string[];
  search_text?: string;
  date_from?: Date;
  date_to?: Date;
  sort_by?: 'uploaded_at' | 'filename' | 'document_type' | 'file_size';
  sort_order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

export interface DocumentSearchResponse {
  documents: DocumentMetadata[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface UploadProgress {
  filename: string;
  progress: number;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  document_id?: string;
  classification?: ClassificationResult;
}

// Upload metadata
export interface UploadMetadata {
  patient_id: string;
  document_type?: DocumentType;
  document_category?: string;
  tags?: string[];
  auto_classify?: boolean;
  auto_generate_filename?: boolean;
}

// Service class
class DocumentService {
  private readonly baseUrl = '/documents';

  /**
   * Upload document with progress tracking
   */
  async uploadDocument(
    file: File, 
    metadata: UploadMetadata,
    onProgress?: (progress: number) => void
  ): Promise<{ document: DocumentMetadata; classification?: ClassificationResult }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', metadata.patient_id);
      
      if (metadata.document_type) {
        formData.append('document_type', metadata.document_type);
      }
      if (metadata.document_category) {
        formData.append('document_category', metadata.document_category);
      }
      if (metadata.tags) {
        formData.append('tags', JSON.stringify(metadata.tags));
      }
      if (metadata.auto_classify !== undefined) {
        formData.append('auto_classify', metadata.auto_classify.toString());
      }
      if (metadata.auto_generate_filename !== undefined) {
        formData.append('auto_generate_filename', metadata.auto_generate_filename.toString());
      }

      const response = await apiClient.post(`${this.baseUrl}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        },
      });

      return response.data;
    } catch (error) {
      console.warn('Backend not available for document upload');
      throw new Error('Soon');
    }
  }

  /**
   * Upload multiple documents with batch progress tracking
   */
  async uploadMultipleDocuments(
    files: File[],
    metadata: UploadMetadata,
    onProgress?: (fileIndex: number, progress: UploadProgress) => void
  ): Promise<Array<{ document: DocumentMetadata; classification?: ClassificationResult; error?: string }>> {
    const results = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      try {
        onProgress?.(i, {
          filename: file.name,
          progress: 0,
          status: 'uploading'
        });

        const result = await this.uploadDocument(file, metadata, (progress) => {
          onProgress?.(i, {
            filename: file.name,
            progress,
            status: 'uploading'
          });
        });

        onProgress?.(i, {
          filename: file.name,
          progress: 100,
          status: 'completed',
          document_id: result.document.document_id,
          classification: result.classification
        });

        results.push(result);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Upload failed';
        
        onProgress?.(i, {
          filename: file.name,
          progress: 0,
          status: 'error',
          error: errorMessage
        });

        results.push({ document: null as any, error: errorMessage });
      }
    }

    return results;
  }

  /**
   * Search documents with advanced filtering
   */
  async searchDocuments(params: DocumentSearchParams): Promise<DocumentSearchResponse> {
    const searchParams = {
      ...params,
      date_from: params.date_from?.toISOString(),
      date_to: params.date_to?.toISOString(),
    };

    const response = await apiClient.post(`${this.baseUrl}/search`, searchParams);
    return response.data;
  }

  /**
   * Get document metadata by ID
   */
  async getDocument(documentId: string): Promise<DocumentMetadata> {
    const response = await apiClient.get(`${this.baseUrl}/${documentId}`);
    return response.data;
  }

  /**
   * Download document as blob
   */
  async downloadDocument(documentId: string): Promise<Blob> {
    const response = await apiClient.get(`${this.baseUrl}/${documentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get document download URL for preview
   */
  getDocumentUrl(documentId: string): string {
    return `${apiClient.getBaseURL()}${this.baseUrl}/${documentId}/download`;
  }

  /**
   * Classify document using AI
   */
  async classifyDocument(text: string): Promise<ClassificationResult> {
    const response = await apiClient.post(`${this.baseUrl}/classify`, {
      text,
    });
    return response.data;
  }

  /**
   * Generate smart filename
   */
  async generateFilename(text: string, originalFilename?: string): Promise<string> {
    const response = await apiClient.post(`${this.baseUrl}/generate-filename`, {
      text,
      original_filename: originalFilename,
    });
    return response.data.filename;
  }

  /**
   * Get document version history
   */
  async getVersionHistory(documentId: string): Promise<VersionInfo[]> {
    const response = await apiClient.get(`${this.baseUrl}/${documentId}/versions`);
    return response.data.versions;
  }

  /**
   * Update document metadata
   */
  async updateDocument(
    documentId: string, 
    updates: Partial<Pick<DocumentMetadata, 'filename' | 'document_type' | 'document_category' | 'tags' | 'metadata'>>
  ): Promise<DocumentMetadata> {
    const response = await apiClient.patch(`${this.baseUrl}/${documentId}`, updates);
    return response.data;
  }

  /**
   * Get health check status
   */
  async getHealthStatus(): Promise<{
    status: string;
    storage_status: string;
    ai_status: string;
    ocr_status: string;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/health`);
    return response.data;
  }

  /**
   * Get document metadata by ID
   */
  async getDocumentMetadata(documentId: string): Promise<DocumentMetadata> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/${documentId}`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available for document metadata');
      throw new Error('Soon');
    }
  }

  /**
   * Update document metadata
   */
  async updateDocumentMetadata(
    documentId: string,
    updates: Partial<Pick<DocumentMetadata, 'filename' | 'document_type' | 'document_category' | 'tags' | 'metadata'>>,
    reason: string
  ): Promise<DocumentMetadata> {
    try {
      const response = await apiClient.patch(`${this.baseUrl}/${documentId}?reason=${encodeURIComponent(reason)}`, updates);
      return response.data;
    } catch (error) {
      console.warn('Backend not available for document update');
      throw new Error('Soon');
    }
  }

  /**
   * Delete document
   */
  async deleteDocument(documentId: string, reason: string, hardDelete = false): Promise<{
    document_id: string;
    deletion_type: string;
    deleted_at: string;
    deleted_by: string;
    reason: string;
    retention_policy_id?: string;
    secure_deletion_scheduled: boolean;
  }> {
    try {
      const params = new URLSearchParams({
        deletion_reason: reason,
        hard_delete: hardDelete.toString()
      });

      const response = await apiClient.delete(`${this.baseUrl}/${documentId}?${params}`);
      return response.data;
    } catch (error) {
      console.warn('Backend not available for document deletion');
      throw new Error('Soon');
    }
  }

  /**
   * Get document statistics
   */
  async getDocumentStats(params?: {
    patient_id?: string;
    date_from?: Date;
    date_to?: Date;
    include_phi?: boolean;
  }): Promise<{
    total_documents: number;
    documents_by_type: Record<DocumentType, number>;
    recent_uploads: DocumentMetadata[];
    storage_usage_bytes: number;
    classification_accuracy: number;
    upload_trends: Record<string, number>;
    access_frequency: Record<string, number>;
  }> {
    try {
      const response = await apiClient.get(`${this.baseUrl}/stats`, params);
      return response.data;
    } catch (error) {
      console.warn('Backend not available for document stats');
      throw new Error('Soon');
    }
  }

  /**
   * Bulk operations
   */
  async bulkDelete(documentIds: string[], reason: string, hardDelete = false): Promise<{
    success_count: number;
    failed_count: number;
    total_count: number;
    failed_documents: Array<{ document_id: string; error: string }>;
    operation_id: string;
    completed_at: string;
  }> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/bulk/delete`, {
        document_ids: documentIds,
        reason: reason,
        hard_delete: hardDelete
      });
      return response.data;
    } catch (error) {
      console.warn('Backend not available for bulk delete');
      throw new Error('Soon');
    }
  }

  async bulkUpdateTags(
    documentIds: string[], 
    tags: string[], 
    action: 'add' | 'remove' | 'replace' = 'replace'
  ): Promise<{
    success_count: number;
    failed_count: number;
    total_count: number;
    failed_documents: Array<{ document_id: string; error: string }>;
    operation_id: string;
    completed_at: string;
  }> {
    try {
      const response = await apiClient.post(`${this.baseUrl}/bulk/update-tags`, {
        document_ids: documentIds,
        tags,
        action
      });
      return response.data;
    } catch (error) {
      console.warn('Backend not available for bulk update tags');
      throw new Error('Soon');
    }
  }

  async bulkUpdateCategory(documentIds: string[], category: string): Promise<{
    success_count: number;
    failed_count: number;
    total_count: number;
    failed_documents: Array<{ document_id: string; error: string }>;
    operation_id: string;
    completed_at: string;
  }> {
    try {
      // Use the existing PATCH endpoint for each document
      const results = await Promise.allSettled(
        documentIds.map(id => 
          this.updateDocumentMetadata(id, { document_category: category }, `Bulk category update to ${category}`)
        )
      );

      const success_count = results.filter(r => r.status === 'fulfilled').length;
      const failed_count = results.filter(r => r.status === 'rejected').length;
      const failed_documents = results
        .map((result, index) => ({ result, index }))
        .filter(({ result }) => result.status === 'rejected')
        .map(({ result, index }) => ({
          document_id: documentIds[index],
          error: result.status === 'rejected' ? result.reason?.message || 'Unknown error' : ''
        }));

      return {
        success_count,
        failed_count,
        total_count: documentIds.length,
        failed_documents,
        operation_id: `bulk_category_${Date.now()}`,
        completed_at: new Date().toISOString()
      };
    } catch (error) {
      console.warn('Backend not available for bulk update category');
      throw new Error('Soon');
    }
  }
}

export const documentService = new DocumentService();