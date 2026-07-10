import { test, expect } from '@playwright/test';

async function createProject(
  request: import('@playwright/test').APIRequestContext,
  name: string,
  email: string,
) {
  const response = await request.post('/api/v1/projects', {
    data: { name, domain: 'automated testing' },
    headers: { 'X-User-Email': email, 'X-User-Name': 'E2E User' },
  });
  expect(response.ok()).toBeTruthy();
  return response.json();
}

test('api health responds', async ({ request }) => {
  const response = await request.get('/api/v1/health');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.status).toBe('healthy');
});

test('connector health includes optional status', async ({ request }) => {
  const response = await request.get('/api/v1/connectors/health');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.optional).toBeDefined();
  expect(Array.isArray(data.registered)).toBeTruthy();
});

test('projects page loads', async ({ page }) => {
  await page.goto('/projects');
  await expect(page.getByText('Active Lab Units')).toBeVisible({ timeout: 30_000 });
});

test('settings page loads', async ({ page }) => {
  await page.goto('/settings');
  await expect(page.getByRole('heading', { name: 'API Settings' })).toBeVisible({
    timeout: 30_000,
  });
});

test('team page loads for created project', async ({ page, request }) => {
  const project = await createProject(request, 'E2E Project', 'e2e@test.com');
  await page.goto(`/projects/${project.id}/team`);
  await expect(page.getByText('Team Collaboration')).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText('Sign In')).toBeVisible();
});

test('papers page loads for created project', async ({ page, request }) => {
  const project = await createProject(request, 'Papers E2E', 'papers-e2e@test.com');
  await page.goto(`/projects/${project.id}/papers`);
  await expect(page.getByText('Literature Corpus')).toBeVisible({ timeout: 30_000 });
});

test('wiki page loads for created project', async ({ page, request }) => {
  const project = await createProject(request, 'Wiki E2E', 'wiki-e2e@test.com');
  await page.goto(`/projects/${project.id}/wiki`);
  await expect(page.getByText('Research Wiki')).toBeVisible({ timeout: 30_000 });
});

test('article studio loads for created project', async ({ page, request }) => {
  const project = await createProject(request, 'Studio E2E', 'studio-e2e@test.com');
  await page.goto(`/projects/${project.id}/article-studio`);
  await expect(page.getByText('Article Studio')).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText('Manuscript')).toBeVisible();
});

test('power analysis API works', async ({ request }) => {
  const project = await createProject(request, 'Power E2E', 'power-e2e@test.com');
  const response = await request.post('/api/v1/sandbox/power-analysis', {
    data: {
      project_id: project.id,
      test_type: 'two_sample_ttest',
      effect_size: 0.5,
    },
    headers: { 'X-User-Email': 'power-e2e@test.com' },
  });
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data.sample_size_per_group).toBeGreaterThan(0);
});

test('keyboard shortcuts button visible', async ({ page }) => {
  await page.goto('/projects');
  await expect(page.getByLabel('Keyboard shortcuts')).toBeVisible({ timeout: 30_000 });
});

test('mobile navigation menu opens', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/projects');
  await page.getByLabel('Open navigation menu').click();
  const mobileDrawer = page.locator('aside.fixed.lg\\:hidden');
  await expect(mobileDrawer.getByRole('link', { name: 'Projects' })).toBeVisible({
    timeout: 10_000,
  });
});