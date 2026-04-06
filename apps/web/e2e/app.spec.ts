import { test, expect } from '@playwright/test';

test.describe('BehaviorSense E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
  });

  test('should load the login page', async ({ page }) => {
    // Check if login page loads
    await expect(page).toHaveURL(/login/);
    await expect(page.getByRole('heading', { name: /登录/i })).toBeVisible();
  });

  test('should navigate to dashboard after login', async ({ page }) => {
    // Fill login form
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should display service status on dashboard', async ({ page }) => {
    // Login first
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();

    // Wait for dashboard
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });

    // Check service status section
    await expect(page.getByText(/服务状态|Service Status/i)).toBeVisible();
  });
});

test.describe('Rules Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should navigate to rules page', async ({ page }) => {
    await page.getByRole('link', { name: /规则|Rules/i }).click();
    await expect(page).toHaveURL(/rules/);
    await expect(page.getByText(/规则列表|Rule List/i)).toBeVisible();
  });

  test('should create a new rule', async ({ page }) => {
    await page.getByRole('link', { name: /规则|Rules/i }).click();
    await page.getByRole('button', { name: /新建|Create/i }).click();

    // Fill rule form
    await page.getByLabel(/规则名称|Rule Name/i).fill('Test Rule');
    await page.getByLabel(/描述|Description/i).fill('E2E Test Rule');

    // Submit
    await page.getByRole('button', { name: /保存|Save/i }).click();

    // Verify success
    await expect(page.getByText(/创建成功|Created/i)).toBeVisible();
  });
});

test.describe('Audit Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should display audit todo list', async ({ page }) => {
    await page.getByRole('link', { name: /审核|Audit/i }).click();
    await expect(page).toHaveURL(/audit/);
    await expect(page.getByText(/待审核|Pending/i)).toBeVisible();
  });

  test('should view audit order details', async ({ page }) => {
    await page.getByRole('link', { name: /审核|Audit/i }).click();

    // Click on first audit item if exists
    const auditItems = page.getByRole('link', { name: /详情|Details/i });
    const count = await auditItems.count();

    if (count > 0) {
      await auditItems.first().click();
      await expect(page).toHaveURL(/audit\/order/);
      await expect(page.getByText(/工单详情|Order Details/i)).toBeVisible();
    }
  });
});

test.describe('User Insight', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should navigate to insight page', async ({ page }) => {
    await page.getByRole('link', { name: /洞察|Insight/i }).click();
    await expect(page).toHaveURL(/insight/);
    await expect(page.getByText(/用户搜索|User Search/i)).toBeVisible();
  });

  test('should search for user', async ({ page }) => {
    await page.getByRole('link', { name: /洞察|Insight/i }).click();

    // Search for user
    await page.getByPlaceholder(/输入用户ID|Enter User ID/i).fill('user_001');
    await page.getByRole('button', { name: /搜索|Search/i }).click();

    // Should show user profile or not found message
    await expect(
      page.getByText(/用户画像|User Profile|未找到|Not Found/i)
    ).toBeVisible();
  });
});

test.describe('Mock Data Generator', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/用户名|username/i).fill('admin');
    await page.getByLabel(/密码|password/i).fill('admin123');
    await page.getByRole('button', { name: /登录|login/i }).click();
    await expect(page).toHaveURL(/dashboard/, { timeout: 10000 });
  });

  test('should navigate to mock page', async ({ page }) => {
    await page.getByRole('link', { name: /模拟|Mock/i }).click();
    await expect(page).toHaveURL(/mock/);
    await expect(page.getByText(/事件生成|Event Generator/i)).toBeVisible();
  });

  test('should generate mock events', async ({ page }) => {
    await page.getByRole('link', { name: /模拟|Mock/i }).click();

    // Set event count
    await page.getByLabel(/事件数量|Event Count/i).fill('10');

    // Click generate
    await page.getByRole('button', { name: /生成|Generate/i }).click();

    // Verify events are generated
    await expect(page.getByText(/生成成功|Generated/i)).toBeVisible();
  });
});
