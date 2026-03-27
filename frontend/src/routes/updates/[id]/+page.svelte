<script lang="ts">
	import { page } from '$app/state';
	import { getUpdate, getReport, type UpdateDetail, type ReportDetail } from '$lib/api/client';
	import { marked } from 'marked';

	let update: UpdateDetail | null = $state(null);
	let report: ReportDetail | null = $state(null);
	let loading = $state(true);
	let error = $state('');
	let lang: 'ko' | 'en' = $state('ko');

	let renderedBody = $derived.by(() => {
		const raw = lang === 'ko' ? report?.body_ko : report?.body_en;
		if (!raw) return '';
		return marked.parse(raw, { async: false }) as string;
	});

	const id = $derived(page.params.id!);

	async function loadData() {
		loading = true;
		error = '';
		try {
			update = await getUpdate(id);
			if (update.report) {
				report = await getReport(update.report.id);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	function typeLabel(type: string): string {
		const labels: Record<string, string> = {
			new_feature: 'New Feature',
			retirement: 'Retirement',
			preview: 'Preview',
			ga: 'GA',
			update: 'Update',
			security: 'Security',
			pricing: 'Pricing',
			deprecation: 'Deprecation',
			guide: 'Guide',
			case_study: 'Case Study',
			announcement: 'Announcement',
			event: 'Event'
		};
		return labels[type] ?? type;
	}

	function typeBadgeClass(type: string): string {
		const classes: Record<string, string> = {
			new_feature: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
			retirement: 'bg-red-50 text-red-700 ring-red-200',
			preview: 'bg-blue-50 text-blue-700 ring-blue-200',
			ga: 'bg-green-50 text-green-700 ring-green-200',
			update: 'bg-amber-50 text-amber-700 ring-amber-200',
			security: 'bg-purple-50 text-purple-700 ring-purple-200',
			pricing: 'bg-orange-50 text-orange-700 ring-orange-200',
			deprecation: 'bg-rose-50 text-rose-700 ring-rose-200',
			guide: 'bg-cyan-50 text-cyan-700 ring-cyan-200',
			case_study: 'bg-teal-50 text-teal-700 ring-teal-200',
			announcement: 'bg-indigo-50 text-indigo-700 ring-indigo-200',
			event: 'bg-pink-50 text-pink-700 ring-pink-200'
		};
		return classes[type] ?? 'bg-gray-50 text-gray-700 ring-gray-200';
	}

	function categoryLabel(s: string): string {
		const labels: Record<string, string> = {
			compute: 'Compute', database: 'Database', ai_ml: 'AI/ML',
			networking: 'Networking', storage: 'Storage', security: 'Security',
			devtools: 'DevTools', analytics: 'Analytics', integration: 'Integration',
			management: 'Management', iot: 'IoT', mixed_reality: 'Mixed Reality', other: 'Other'
		};
		return labels[s] ?? s;
	}

	function statusLabel(status: string): string {
		const labels: Record<string, string> = {
			completed: '✅ 완료',
			pending: '⏳ 대기',
			failed: '❌ 실패',
			in_progress: '🔄 진행 중'
		};
		return labels[status] ?? status;
	}

	$effect(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>{update?.title ?? 'Loading...'} — Microsoft News</title>
</svelte:head>

{#if loading}
	<div class="flex flex-col items-center justify-center py-20 gap-3">
		<div class="h-8 w-8 animate-spin rounded-full border-[3px] border-[var(--color-primary-ring)] border-t-[var(--color-primary)]"></div>
		<span class="text-sm text-[var(--color-text-subtle)]">불러오는 중...</span>
	</div>
{:else if error}
	<div class="rounded-2xl bg-red-50 p-5 text-sm text-red-600 ring-1 ring-red-100">
		{error}
	</div>
{:else if update}
	<!-- Back link -->
	<a href="/" class="inline-flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] mb-8 transition-colors group">
		<svg class="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
		목록으로 돌아가기
	</a>

	<!-- Update header -->
	<div class="rounded-xl bg-[var(--color-surface)] p-8 mb-6 border border-[var(--color-border-strong)]">
		<!-- Type badges -->
		{#if update.update_type && update.update_type.length > 0}
			<div class="flex flex-wrap gap-2 mb-5">
				{#each update.update_type as type}
					<span class="rounded-full px-3 py-1 text-xs font-semibold ring-1 {typeBadgeClass(type)}">
						{typeLabel(type)}
					</span>
				{/each}
			</div>
		{/if}

		<h1 class="text-2xl font-extrabold text-[var(--color-text)] leading-tight">{update.title_ko || update.title}</h1>
		{#if update.title_ko}
			<p class="mt-2 text-sm text-[var(--color-text-subtle)]">{update.title}</p>
		{/if}

		{#if update.summary_ko || update.summary}
			<p class="mt-4 text-[var(--color-text-muted)] leading-relaxed">{update.summary_ko || update.summary}</p>
		{/if}

		<!-- Meta info -->
		<div class="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 pt-5 border-t border-[var(--color-border)]">
			<div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
				<svg class="w-4 h-4 text-[var(--color-text-subtle)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
				{formatDate(update.published_date)}
			</div>
			{#if update.categories && update.categories.length > 0}
				<div class="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
					<svg class="w-4 h-4 text-[var(--color-text-subtle)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z"/></svg>
					{update.categories.map(c => categoryLabel(c)).join(', ')}
				</div>
			{/if}
			{#if update.source_url}
				<a href={update.source_url} target="_blank" rel="noopener"
					class="flex items-center gap-1.5 text-sm font-medium text-[var(--color-primary)] hover:underline ml-auto">
					원문 보기
					<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg>
				</a>
			{/if}
		</div>
	</div>

	<!-- Services affected -->
	{#if update.services_affected && update.services_affected.length > 0}
		<div class="mb-6">
			<h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-subtle)] mb-3">영향 받는 서비스</h3>
			<div class="flex flex-wrap gap-2">
				{#each update.services_affected as service}
					<span class="rounded-xl px-3.5 py-1.5 text-sm font-medium ring-1"
						style="background: var(--color-primary-light); color: var(--color-primary); ring-color: var(--color-primary-ring);">
						{service}
					</span>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Report section -->
	{#if report}
		<!-- Language toggle -->
		<div class="flex items-center gap-2 mb-5">
			<h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-subtle)] mr-2">분석 리포트</h3>
			<button
				onclick={() => lang = 'ko'}
				class="rounded-full px-4 py-1.5 text-sm font-medium transition-all active:scale-95
					{lang === 'ko' ? '' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-primary-subtle)]'}"
				style={lang === 'ko' ? 'background: var(--color-primary); color: var(--color-primary-fg);' : ''}
			>
				🇰🇷 한국어
			</button>
			<button
				onclick={() => lang = 'en'}
				class="rounded-full px-4 py-1.5 text-sm font-medium transition-all active:scale-95
					{lang === 'en' ? '' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-primary-subtle)]'}"
				style={lang === 'en' ? 'background: var(--color-primary); color: var(--color-primary-fg);' : ''}
			>
				🇺🇸 English
			</button>
			<span class="ml-auto text-xs text-[var(--color-text-subtle)]">
				{statusLabel(report.status)}
				{#if report.model_used}
					· <span class="font-mono">{report.model_used}</span>
				{/if}
			</span>
		</div>

		<!-- Report content -->
		<div class="rounded-xl bg-[var(--color-surface)] p-8 border border-[var(--color-border-strong)]">
			<h2 class="text-xl font-extrabold text-[var(--color-text)] mb-3">
				{lang === 'ko' ? report.title_ko : report.title_en}
			</h2>
			<p class="text-[var(--color-text-muted)] mb-6 text-sm leading-relaxed border-l-4 pl-4 py-2 rounded-r-lg"
				style="border-color: var(--color-primary-ring); background: var(--color-primary-light);">
				{lang === 'ko' ? report.summary_ko : report.summary_en}
			</p>

			{#if report.affected_services && Array.isArray(report.affected_services) && report.affected_services.length > 0}
				<div class="mb-6 flex flex-wrap gap-2">
					{#each report.affected_services as service}
						<span class="rounded-xl px-3 py-1 text-xs font-medium ring-1"
							style="background: var(--color-primary-light); color: var(--color-primary); ring-color: var(--color-primary-ring);">
							{service}
						</span>
					{/each}
				</div>
			{/if}

			<div class="prose prose-sm max-w-none text-[var(--color-text)] leading-relaxed
				prose-headings:font-extrabold prose-headings:text-[var(--color-text)]
				prose-a:text-[var(--color-primary)] prose-a:no-underline hover:prose-a:underline
				prose-code:text-[var(--color-primary)] prose-code:bg-[var(--color-primary-light)] prose-code:rounded prose-code:px-1">
				{@html renderedBody}
			</div>
		</div>

	{:else}
		<div class="rounded-2xl bg-amber-50 p-6 text-sm text-amber-700 ring-1 ring-amber-100 flex items-center gap-3">
			<span class="text-xl">📝</span>
			이 업데이트에 대한 분석 리포트가 아직 생성되지 않았습니다.
		</div>
	{/if}
{/if}