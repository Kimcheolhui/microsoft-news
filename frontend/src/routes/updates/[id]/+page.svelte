<script lang="ts">
	import { page } from '$app/state';
	import { getUpdate, getReport, type UpdateDetail, type ReportDetail } from '$lib/api/client';

	let update: UpdateDetail | null = $state(null);
	let report: ReportDetail | null = $state(null);
	let loading = $state(true);
	let error = $state('');
	let lang: 'ko' | 'en' = $state('ko');

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
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	function typeLabel(type: string | null): string {
		const labels: Record<string, string> = {
			new_feature: '🆕 신규 기능',
			retirement: '🔴 서비스 종료',
			preview: '🔵 프리뷰',
			ga: '🟢 정식 출시 (GA)',
			update: '🔄 업데이트'
		};
		return type ? labels[type] ?? type : '분류 없음';
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
	<title>{update?.title ?? 'Loading...'} — Azure Ingest</title>
</svelte:head>

{#if loading}
	<div class="flex justify-center py-16">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent"></div>
	</div>
{:else if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
		{error}
	</div>
{:else if update}
	<!-- Back link -->
	<a href="/" class="inline-flex items-center gap-1 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-primary)] mb-6">
		← 목록으로
	</a>

	<!-- Update header -->
	<div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6 mb-6">
		<h1 class="text-2xl font-bold text-[var(--color-text)]">{update.title}</h1>
		<div class="mt-3 flex flex-wrap items-center gap-3 text-sm text-[var(--color-text-muted)]">
			<span>{formatDate(update.published_date)}</span>
			<span>·</span>
			<span>{typeLabel(update.update_type)}</span>
			{#if update.source_url}
				<span>·</span>
				<a href={update.source_url} target="_blank" rel="noopener"
					class="text-[var(--color-primary)] hover:underline">
					원문 보기 ↗
				</a>
			{/if}
		</div>
		{#if update.summary}
			<p class="mt-4 text-[var(--color-text-muted)]">{update.summary}</p>
		{/if}
	</div>

	<!-- Report section -->
	{#if report}
		<!-- Language toggle -->
		<div class="flex items-center gap-2 mb-4">
			<button
				onclick={() => lang = 'ko'}
				class="rounded-lg px-4 py-2 text-sm font-medium transition-colors
					{lang === 'ko' ? 'bg-[var(--color-primary)] text-white' : 'border border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-gray-50'}"
			>
				🇰🇷 한국어
			</button>
			<button
				onclick={() => lang = 'en'}
				class="rounded-lg px-4 py-2 text-sm font-medium transition-colors
					{lang === 'en' ? 'bg-[var(--color-primary)] text-white' : 'border border-[var(--color-border)] text-[var(--color-text-muted)] hover:bg-gray-50'}"
			>
				🇺🇸 English
			</button>
			<span class="ml-auto text-xs text-[var(--color-text-muted)]">
				{statusLabel(report.status)}
				{#if report.model_used}
					· {report.model_used}
				{/if}
			</span>
		</div>

		<!-- Report content -->
		<div class="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
			<h2 class="text-xl font-bold text-[var(--color-text)] mb-2">
				{lang === 'ko' ? report.title_ko : report.title_en}
			</h2>
			<p class="text-[var(--color-text-muted)] mb-6 text-sm">
				{lang === 'ko' ? report.summary_ko : report.summary_en}
			</p>

			{#if report.affected_services && Array.isArray(report.affected_services) && report.affected_services.length > 0}
				<div class="mb-6 flex flex-wrap gap-1.5">
					{#each report.affected_services as service}
						<span class="rounded-full bg-blue-50 border border-blue-200 px-2.5 py-0.5 text-xs font-medium text-blue-700">
							{service}
						</span>
					{/each}
				</div>
			{/if}

			<div class="prose prose-sm max-w-none text-[var(--color-text)]">
				{@html (lang === 'ko' ? report.body_ko : report.body_en)?.replace(/\n/g, '<br>') ?? ''}
			</div>
		</div>

		<!-- Pipeline runs -->
		{#if report.runs && report.runs.length > 0}
			<details class="mt-6">
				<summary class="cursor-pointer text-sm font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text)]">
					파이프라인 실행 내역 ({report.runs.length}단계)
				</summary>
				<div class="mt-3 space-y-2">
					{#each report.runs as run}
						<div class="flex items-center gap-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2.5 text-sm">
							<span class="font-mono font-medium">{run.step}</span>
							<span class="text-[var(--color-text-muted)]">{statusLabel(run.status)}</span>
							{#if run.tokens_used}
								<span class="text-xs text-[var(--color-text-muted)]">{run.tokens_used} tokens</span>
							{/if}
							{#if run.error}
								<span class="text-xs text-red-600">Error</span>
							{/if}
						</div>
					{/each}
				</div>
			</details>
		{/if}
	{:else}
		<div class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-700">
			이 업데이트에 대한 분석 리포트가 아직 생성되지 않았습니다.
		</div>
	{/if}
{/if}