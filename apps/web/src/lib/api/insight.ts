import { insightApi } from './client';
import type { ApiResponse } from '@/types/api';
import type { User, UserTag, UserProfile } from '@/types/user';

export interface UserTagsResponse {
  userId: string;
  tags: Record<string, UserTag>;
  lastUpdateTime: string;
}

export interface UserProfileResponse {
  userId: string;
  basicInfo: {
    registerTime: string;
    region?: string;
    lastActiveTime?: string;
  };
  behaviorTags: string[];
  statTags: string[];
  riskProfile: Record<string, unknown>;
  preferenceProfile: Record<string, unknown>;
}

export interface TagStatistics {
  tagName: string;
  total: number;
  distribution: Record<string, number>;
}

export interface UpdateTagInput {
  tagName: string;
  tagValue: string;
  source: 'manual';
  operator: string;
}

export interface BatchTagsRequest {
  userIds: string[];
  tagNames: string[];
}

export interface BatchTagsResponse {
  userId: string;
  tags: Record<string, UserTag>;
}

export const insightService = {
  // Get user tags
  getUserTags: (userId: string) =>
    insightApi
      .get(`user/${userId}/tags`)
      .json<ApiResponse<UserTagsResponse>>(),

  // Get user profile
  getUserProfile: (userId: string) =>
    insightApi
      .get(`user/${userId}/profile`)
      .json<ApiResponse<UserProfileResponse>>(),

  // Batch query user tags
  batchGetUserTags: (data: BatchTagsRequest) =>
    insightApi
      .post('user/tags/batch', { json: data })
      .json<ApiResponse<BatchTagsResponse[]>>(),

  // Update user tag manually
  updateUserTag: (userId: string, data: UpdateTagInput) =>
    insightApi
      .put(`user/${userId}/tag`, { json: data })
      .json<ApiResponse<null>>(),

  // Get tag statistics
  getTagStatistics: (tagName: string) =>
    insightApi
      .get('tags/statistics', {
        searchParams: { tagName },
      })
      .json<ApiResponse<TagStatistics>>(),
};
