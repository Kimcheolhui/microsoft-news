<script lang="ts">
	import { getUpdates, getSources, type UpdateSummary, type Source } from '$lib/api/client';
	import DateRangePicker from '$lib/components/DateRangePicker.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	let updates: UpdateSummary[] = $state([]);
	let sources: Source[] = $state([]);
	let total = $state(0);
	let currentPage = $state(1);
	let pageSize = 20;
	let loading = $state(true);
	let error = $state('');

	// Filters
	let searchQuery = $state('');
	let selectedSource = $state('');
	let selectedType = $state('');
	let dateFrom = $state('');
	let dateTo = $state('');
	let datePickerRef: DateRangePicker;

	const updateTypes = ['new_feature', 'retirement', 'preview', 'ga', 'update', 'security', 'pricing', 'deprecation', 'guide', 'case_study', 'announcement', 'event'];

	let totalPages = $derived(Math.ceil(total / pageSize));

	async function loadUpdates() {
		loading = true;
		error = '';
		try {
			const data = await getUpdates({
				page: currentPage,
				page_size: pageSize,
				source_id: selectedSource || undefined,
				update_type: selectedType || undefined,
				q: searchQuery || undefined,
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined
			});
			updates = data.items;
			total = data.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load updates';
		} finally {
			loading = false;
		}
	}

	async function loadSources() {
		try {
			sources = await getSources();
		} catch {
			// Sources filter won't work but page still loads
		}
	}

	function applyFilters() {
		currentPage = 1;
		loadUpdates();
	}

	function clearFilters() {
		searchQuery = '';
		selectedSource = '';
		selectedType = '';
		dateFrom = '';
		dateTo = '';
		datePickerRef?.clear();
		currentPage = 1;
		loadUpdates();
	}

	function goToPage(p: number) {
		currentPage = p;
		loadUpdates();
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function capitalize(s: string): string {
		return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ');
	}

	function typeLabel(type: string): string {
		const labels: Record<string, string> = {
			new_feature: '🆕 신규',
			retirement: '🔴 종료',
			preview: '🔵 프리뷰',
			ga: '🟢 GA',
			update: '🔄 업데이트',
			security: '🔒 보안',
			pricing: '💰 가격',
			deprecation: '⚠️ 중단 예고',
			guide: '📖 가이드',
			case_study: '💡 사용 사례',
			announcement: '📢 공지',
			event: '🎪 이벤트'
		};
		return labels[type] ?? type;
	}

	function typeBadgeClass(type: string): string {
		const classes: Record<string, string> = {
			new_feature: 'bg-emerald-100 text-emerald-800',
			retirement: 'bg-red-100 text-red-800',
			preview: 'bg-blue-100 text-blue-800',
			ga: 'bg-green-100 text-green-800',
			update: 'bg-amber-100 text-amber-800',
			security: 'bg-purple-100 text-purple-800',
			pricing: 'bg-orange-100 text-orange-800',
			deprecation: 'bg-rose-100 text-rose-800',
			guide: 'bg-cyan-100 text-cyan-800',
			case_study: 'bg-teal-100 text-teal-800',
			announcement: 'bg-indigo-100 text-indigo-800',
			event: 'bg-pink-100 text-pink-800'
		};
		return classes[type] ?? 'bg-gray-100 text-gray-800';
	}

	$effect(() => {
		loadSources();
		loadUpdates();
	});
</script>

<!-- Hero -->
<section class="relative mb-8 overflow-hidden rounded-2xl bg-gradient-to-br from-[#0078d4] to-[#005a9e] px-8 py-12 text-white">
	<div class="absolute inset-0 bg-[url('/hero-bg.webp')] bg-cover bg-center opacity-20"></div>
	<div class="relative">
		<h1 class="text-3xl font-bold tracking-tight">Azure News</h1>
		<p class="mt-2 max-w-xl text-base text-white/85">
			Azure 생태계의 최신 업데이트, 신규 기능, 보안 공지를 한눈에 확인하세요.<br />
			AI 기반 심층 분석 리포트로 변화의 핵심을 빠르게 파악할 수 있습니다.
		</p>
	</div>
</section>

<!-- Search & Filters -->
<div class="mb-6 space-y-3">
	<div class="flex items-center gap-2">
		<input
			type="text"
			placeholder="검색..."
			bind:value={searchQuery}
			onkeydown={(e) => e.key === 'Enter' && applyFilters()}
			class="min-w-0 flex-1 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm
				focus:border-[var(--color-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
		/>
		<select
			bind:value={selectedSource}
			onchange={applyFilters}
			class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm bg-white
				focus:border-[var(--color-primary)] focus:outline-none"
		>
			<option value="">모든 소스</option>
			{#each sources as source}
				<option value={source.id}>{source.display_name || source.name}</option>
			{/each}
		</select>
		<select
			bind:value={selectedType}
			onchange={applyFilters}
			class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm bg-white
				focus:border-[var(--color-primary)] focus:outline-none"
		>
			<option value="">모든 유형</option>
			{#each updateTypes as type}
				<option value={type}>{typeLabel(type)}</option>
			{/each}
		</select>
		<DateRangePicker
			bind:this={datePickerRef}
			{dateFrom}
			{dateTo}
			onchange={(from, to) => { dateFrom = from; dateTo = to; applyFilters(); }}
		/>
		<button
			onclick={applyFilters}
			class="shrink-0 rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm font-medium text-white
				hover:bg-[var(--color-primary-hover)] transition-colors"
		>
			검색
		</button>
		{#if searchQuery || selectedSource || selectedType || dateFrom || dateTo}
			<button
				onclick={clearFilters}
				class="shrink-0 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm text-[var(--color-text-muted)]
					hover:bg-gray-50 transition-colors"
			>
				초기화
			</button>
		{/if}
	</div>
	<p class="text-sm text-[var(--color-text-muted)]">
		총 <strong class="text-[var(--color-text)]">{total}</strong>건
	</p>
</div>

<!-- Update List -->
{#if loading}
	<div class="flex justify-center py-16">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-[var(--color-primary)] border-t-transparent"></div>
	</div>
{:else if error}
	<div class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
		{error}
	</div>
{:else if updates.length === 0}
	<div class="py-16 text-center text-[var(--color-text-muted)]">
		업데이트가 없습니다.
	</div>
{:else}
	<div class="space-y-3">
		{#each updates as update}
			<a
				href="/updates/{update.id}"
				class="block rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-5
					hover:border-[var(--color-primary)] hover:shadow-sm transition-all"
			>
				<div class="flex items-start justify-between gap-3">
					<div class="min-w-0 flex-1">
						<h3 class="text-base font-medium text-[var(--color-text)] truncate">{update.title_ko || update.title}</h3>
						{#if update.title_ko}
							<p class="mt-1 text-xs text-[var(--color-text-muted)] truncate">{update.title}</p>
						{/if}
						{#if update.summary_ko || update.summary}
							<p class="mt-2 text-sm text-[var(--color-text-muted)] line-clamp-2">{update.summary_ko || update.summary}</p>
						{/if}
					</div>
					{#if update.update_type && update.update_type.length > 0}
						<div class="shrink-0 flex flex-wrap gap-1 justify-end">
							{#each update.update_type as type}
								<span class="rounded-full px-2.5 py-0.5 text-xs font-medium {typeBadgeClass(type)}">
									{typeLabel(type)}
								</span>
							{/each}
						</div>
					{/if}
				</div>
				<div class="mt-3 flex items-center gap-4 text-xs text-[var(--color-text-muted)]">
					<span>{formatDate(update.published_date)}</span>
					{#if update.categories && update.categories.length > 0}
						<span>·</span>
						<span>{update.categories.map(c => capitalize(c)).join(', ')}</span>
					{/if}
				</div>
			</a>
		{/each}
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="mt-6 flex items-center justify-center gap-2">
			<button
				onclick={() => goToPage(currentPage - 1)}
				disabled={currentPage <= 1}
				class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm
					hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
			>
				← 이전
			</button>
			<span class="px-3 text-sm text-[var(--color-text-muted)]">
				{currentPage} / {totalPages}
			</span>
			<button
				onclick={() => goToPage(currentPage + 1)}
				disabled={currentPage >= totalPages}
				class="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm
					hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
			>
				다음 →
			</button>
		</div>
	{/if}
{/if}
