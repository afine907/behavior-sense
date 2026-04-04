export interface User {
  userId: string;
  tags: Record<string, UserTag>;
  profile?: UserProfile;
}

export interface UserTag {
  value: string;
  updateTime: string;
  source: 'auto' | 'manual';
}

export interface UserProfile {
  registerTime: string;
  region?: string;
  lastActiveTime: string;
}

export interface UserListParams {
  page?: number;
  size?: number;
  tagKey?: string;
  tagValue?: string;
}
