// Auth hooks
export {
  useLogin,
  useLogout,
  useCurrentUser,
  useIsAuthenticated,
  useHasRole,
} from './use-auth';

// Rules hooks
export {
  rulesKeys,
  useRules,
  useRule,
  useCreateRule,
  useUpdateRule,
  useDeleteRule,
  useToggleRule,
  useTestRule,
} from './use-rules';

// Audit hooks
export {
  auditKeys,
  useAuditOrders,
  useAuditTodo,
  useAuditOrder,
  useAuditStats,
  useCreateAuditOrder,
  useReviewAuditOrder,
  useApproveAuditOrder,
  useRejectAuditOrder,
} from './use-audit';

// Insight hooks
export {
  insightKeys,
  useUserTags,
  useUserProfile,
  useTagStatistics,
  useBatchUserTags,
  useUpdateUserTag,
} from './use-insight';

// Mock hooks
export {
  mockKeys,
  useGenerateEvents,
  useStartScenario,
  useStopScenario,
  useScenario,
  useScenarios,
} from './use-mock';

// Dashboard hooks
export {
  dashboardKeys,
  useDashboardMetrics,
  useServiceHealth,
  useEventTrend,
  useRecentActivity,
  type DashboardMetrics,
  type ServiceHealth,
  type EventTrendPoint,
  type RecentActivityItem,
} from './use-dashboard';
