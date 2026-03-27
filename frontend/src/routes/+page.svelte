<script lang="ts">
	import { getUpdates, getSources, type UpdateSummary, type Source } from '$lib/api/client';
	import DateRangePicker from '$lib/components/DateRangePicker.svelte';
	import FilterSelect from '$lib/components/FilterSelect.svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { untrack } from 'svelte';

	let updates: UpdateSummary[] = $state([]);
	let sources: Source[] = $state([]);
	let total = $state(0);
	let currentPage = $state(1);
	let pageSize = 20;
	let loading = $state(true);
	let error = $state('');

	// Filters
	let searchQuery = $state('');
	let selectedSources: string[] = $state([]);
	let selectedType = $state('');
	let selectedCategory = $state('');
	let dateFrom = $state('');
	let dateTo = $state('');
	let datePickerRef: DateRangePicker;

	const updateTypeOptions = [
		{ value: 'new_feature', label: 'New Feature' },
		{ value: 'retirement', label: 'Retirement' },
		{ value: 'preview', label: 'Preview' },
		{ value: 'ga', label: 'GA' },
		{ value: 'update', label: 'Update' },
		{ value: 'security', label: 'Security' },
		{ value: 'pricing', label: 'Pricing' },
		{ value: 'deprecation', label: 'Deprecation' },
		{ value: 'guide', label: 'Guide' },
		{ value: 'case_study', label: 'Case Study' },
		{ value: 'announcement', label: 'Announcement' },
		{ value: 'event', label: 'Event' },
	];

	const categoryOptions = [
		{ value: 'compute', label: 'Compute' },
		{ value: 'database', label: 'Database' },
		{ value: 'ai_ml', label: 'AI/ML' },
		{ value: 'networking', label: 'Networking' },
		{ value: 'storage', label: 'Storage' },
		{ value: 'security', label: 'Security' },
		{ value: 'devtools', label: 'DevTools' },
		{ value: 'analytics', label: 'Analytics' },
		{ value: 'integration', label: 'Integration' },
		{ value: 'management', label: 'Management' },
		{ value: 'iot', label: 'IoT' },
		{ value: 'mixed_reality', label: 'Mixed Reality' },
		{ value: 'other', label: 'Other' },
	];

	function toggleSource(name: string) {
		if (selectedSources.includes(name)) {
			selectedSources = selectedSources.filter((s) => s !== name);
		} else {
			selectedSources = [...selectedSources, name];
		}
	}

	/** Unified style for source buttons */
	const sourceBrandActive = {
		classes: 'ring-1',
	};

	/** Left border color for update cards based on first type */
	function cardAccentColor(types: string[] | null): string {
		if (!types || types.length === 0) return 'border-l-gray-200';
		const map: Record<string, string> = {
			new_feature: 'border-l-emerald-400',
			retirement: 'border-l-red-400',
			preview: 'border-l-blue-400',
			ga: 'border-l-green-500',
			update: 'border-l-amber-400',
			security: 'border-l-purple-400',
			pricing: 'border-l-orange-400',
			deprecation: 'border-l-rose-400',
			guide: 'border-l-cyan-400',
			case_study: 'border-l-teal-400',
			announcement: 'border-l-indigo-400',
			event: 'border-l-pink-400',
		};
		return map[types[0]] ?? 'border-l-gray-300';
	}

	let totalPages = $derived(Math.ceil(total / pageSize));

	function pushFiltersToURL() {
		const params = new URLSearchParams();
		if (searchQuery) params.set('q', searchQuery);
		if (selectedSources.length > 0) params.set('source', selectedSources.join(','));
		if (selectedType) params.set('type', selectedType);
		if (selectedCategory) params.set('category', selectedCategory);
		if (dateFrom) params.set('date_from', dateFrom);
		if (dateTo) params.set('date_to', dateTo);
		if (currentPage > 1) params.set('page', String(currentPage));
		const qs = params.toString();
		goto(qs ? `?${qs}` : '/', { keepFocus: true, noScroll: true });
	}

	async function loadUpdatesFromParams(params: URLSearchParams) {
		loading = true;
		error = '';
		try {
			const data = await getUpdates({
				page: parseInt(params.get('page') || '1', 10),
				page_size: pageSize,
				sources: params.get('source')?.split(',').filter(Boolean) || undefined,
				update_type: params.get('type') || undefined,
				category: params.get('category') || undefined,
				q: params.get('q') || undefined,
				date_from: params.get('date_from') || undefined,
				date_to: params.get('date_to') || undefined
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
		pushFiltersToURL();
	}

	function clearFilters() {
		searchQuery = '';
		selectedSources = [];
		selectedType = '';
		selectedCategory = '';
		dateFrom = '';
		dateTo = '';
		currentPage = 1;
		datePickerRef?.setDates('', '');
		goto('/', { keepFocus: true, noScroll: true });
	}

	function goToPage(p: number) {
		currentPage = p;
		pushFiltersToURL();
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function categoryLabel(s: string): string {
		const labels: Record<string, string> = {
			compute: 'Compute',
			database: 'Database',
			ai_ml: 'AI/ML',
			networking: 'Networking',
			storage: 'Storage',
			security: 'Security',
			devtools: 'DevTools',
			analytics: 'Analytics',
			integration: 'Integration',
			management: 'Management',
			iot: 'IoT',
			mixed_reality: 'Mixed Reality',
			other: 'Other'
		};
		return labels[s] ?? s;
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

	// Load sources once
	$effect(() => {
		loadSources();
	});

	// React to URL changes: sync filter state and load data
	$effect(() => {
		const params = page.url.searchParams;

		searchQuery = params.get('q') || '';
		selectedSources = params.get('source')?.split(',').filter(Boolean) || [];
		selectedType = params.get('type') || '';
		selectedCategory = params.get('category') || '';
		dateFrom = params.get('date_from') || '';
		dateTo = params.get('date_to') || '';
		currentPage = parseInt(params.get('page') || '1', 10);

		const df = params.get('date_from') || '';
		const dt = params.get('date_to') || '';
		untrack(() => datePickerRef?.setDates(df, dt));

		loadUpdatesFromParams(params);
	});
</script>

<!-- Hero -->
<section class="mb-12 pt-2">
	<h1 class="text-3xl font-bold tracking-tight text-[var(--color-text)] leading-tight">Microsoft News</h1>
	<p class="mt-3 max-w-xl text-[15px] text-[var(--color-text-muted)] leading-relaxed">
		Azure, GitHub, Fabric 등 Microsoft 생태계의 최신 업데이트를 수집하고,
		AI 분석 리포트로 핵심을 빠르게 파악합니다.
	</p>
</section>

<!-- Source Toggle Buttons -->
{#if sources.length > 0}
	<div class="flex flex-wrap items-center gap-2 mb-8">
		<span class="text-sm font-medium uppercase tracking-wider text-[var(--color-text-subtle)] mr-1">Sources</span>
		{#each sources as src}
			<button
				onclick={() => toggleSource(src.name)}
				class="source-btn cursor-pointer rounded-full px-4 py-2.5 text-[15px] font-medium transition-all duration-150 select-none
					active:scale-95
					{selectedSources.includes(src.name)
						? sourceBrandActive.classes + ' source-btn-active'
						: 'text-[var(--color-text-muted)] source-btn-inactive'}"
				style="{selectedSources.includes(src.name)
					? 'background: var(--color-primary); color: var(--color-primary-fg); box-shadow: 0 3px 10px rgba(0,0,0,0.12);'
					: 'background: var(--color-surface); box-shadow: 0 2px 6px rgba(0,0,0,0.08);'}"
			>
				{src.display_name || src.name}
			</button>
		{/each}
	</div>
{/if}

<!-- Search & Filters -->
<div class="mb-8 rounded-xl bg-[var(--color-surface)] p-6 shadow-[0_3px_10px_rgba(0,0,0,0.12)]">
	<div class="flex items-center gap-3 mb-3">
		<div class="relative flex-1">
			<svg class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-subtle)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
			</svg>
			<input
				type="text"
				placeholder="키워드로 검색..."
				bind:value={searchQuery}
				onkeydown={(e) => e.key === 'Enter' && applyFilters()}
				class="w-full rounded-lg bg-[var(--color-primary-subtle)] pl-11 pr-4 text-sm text-[var(--color-text)]
					border-none placeholder:text-[var(--color-text-subtle)]
					focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none transition-shadow"
				style="height: 44px;"
			/>
		</div>
		{#if searchQuery || selectedSources.length > 0 || selectedType || selectedCategory || dateFrom || dateTo}
			<button
				onclick={clearFilters}
			class="shrink-0 cursor-pointer rounded-lg px-4 py-2.5 text-sm text-[var(--color-text-muted)]
				bg-[var(--color-primary-subtle)] hover:bg-[var(--color-primary-muted)] transition-colors"
			>
				초기화
			</button>
		{/if}
		<button
			onclick={applyFilters}
			class="shrink-0 cursor-pointer rounded-lg px-5 py-2.5 text-sm font-medium
				active:scale-[0.98] transition-all"
			style="background: var(--color-primary); color: var(--color-primary-fg);"
		>
			적용
		</button>
	</div>
	<div class="flex items-center gap-4">
		<div class="w-0 flex-1">
			<FilterSelect
				options={updateTypeOptions}
				bind:value={selectedType}
				placeholder="All types"
			/>
		</div>
		<div class="w-0 flex-1">
			<FilterSelect
				options={categoryOptions}
				bind:value={selectedCategory}
				placeholder="All categories"
			/>
		</div>
		<div class="w-0 flex-1">
			<DateRangePicker
				bind:this={datePickerRef}
				{dateFrom}
				{dateTo}
				onchange={(from, to) => { dateFrom = from; dateTo = to; }}
			/>
		</div>
	</div>
</div>

<!-- Results count -->
<div class="flex justify-between items-center mb-4">
	<span class="text-xs font-medium text-[var(--color-text-subtle)]">
		<strong class="text-[var(--color-text)]">{total}</strong>건의 업데이트
	</span>
</div>

<!-- Update List -->
{#if loading}
	<div class="flex flex-col items-center justify-center py-20 gap-3">
		<div class="h-8 w-8 animate-spin rounded-full border-[3px] border-[var(--color-primary-ring)] border-t-[var(--color-primary)]"></div>
		<span class="text-sm text-[var(--color-text-subtle)]">불러오는 중...</span>
	</div>
{:else if error}
	<div class="rounded-2xl bg-red-50 p-5 text-sm text-red-600 ring-1 ring-red-100">
		{error}
	</div>
{:else if updates.length === 0}
	<div class="py-20 text-center">
		<span class="text-4xl mb-4 block">🔍</span>
		<p class="text-[var(--color-text-muted)]">일치하는 업데이트가 없습니다.</p>
	</div>
{:else}
	<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
		{#each updates as update}
			<a
				href="/updates/{update.id}"
				class="group block rounded-lg bg-[var(--color-surface)] p-6 border-l-[3px] {cardAccentColor(update.update_type)}
					shadow-[0_3px_10px_rgba(0,0,0,0.12)]
					hover:shadow-[0_6px_16px_rgba(0,0,0,0.16)] hover:bg-[var(--color-surface-raised)]
					transition-all duration-150"
			>
				{#if update.update_type && update.update_type.length > 0}
					<div class="flex flex-wrap gap-1.5 mb-3">
						{#each update.update_type as type}
							<span class="rounded-full px-3 py-1 text-xs font-semibold ring-1 {typeBadgeClass(type)}">
								{typeLabel(type)}
							</span>
						{/each}
					</div>
				{/if}
				<h3 class="text-[20px] font-semibold text-[var(--color-text)] leading-snug group-hover:opacity-70 transition-opacity">
					{update.title_ko || update.title}
				</h3>
				{#if update.title_ko}
					<p class="mt-2 text-xs text-[var(--color-text-subtle)] truncate">{update.title}</p>
				{/if}
				{#if update.summary_ko || update.summary}
					<p class="mt-3.5 text-sm text-[var(--color-text-muted)] line-clamp-2 leading-relaxed">
						{update.summary_ko || update.summary}
					</p>
				{/if}
				<div class="mt-5 flex items-center gap-3 text-xs text-[var(--color-text-subtle)]">
					<span class="font-medium">{formatDate(update.published_date)}</span>
					{#if update.services_affected && update.services_affected.length > 0}
						<span class="text-[var(--color-border-hover)]">·</span>
						<div class="flex gap-1">
							{#each update.services_affected.slice(0, 3) as service}
								<span class="rounded-md px-1.5 py-0.5 text-[11px] font-medium"
									style="background: var(--color-primary-light); color: var(--color-primary);">
									{service}
								</span>
							{/each}
							{#if update.services_affected.length > 3}
								<span class="text-[var(--color-text-subtle)]">+{update.services_affected.length - 3}</span>
							{/if}
						</div>
					{/if}
					{#if update.categories && update.categories.length > 0}
						<span class="text-[var(--color-border-hover)]">·</span>
						<span>{update.categories.map(c => categoryLabel(c)).join(', ')}</span>
					{/if}
				</div>
			</a>
		{/each}
	</div>

	<!-- Pagination -->
	{#if totalPages > 1}
		<div class="mt-10 flex items-center justify-center gap-1">
			<button
				onclick={() => goToPage(currentPage - 1)}
				disabled={currentPage <= 1}
				class="cursor-pointer rounded-lg px-3 py-2 text-sm text-[var(--color-text-muted)]
					hover:bg-[var(--color-primary-subtle)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
			>
				←
			</button>
			{#each Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
				if (totalPages <= 7) return i + 1;
				if (currentPage <= 4) return i + 1;
				if (currentPage >= totalPages - 3) return totalPages - 6 + i;
				return currentPage - 3 + i;
			}) as p}
				<button
					onclick={() => goToPage(p)}
				class="cursor-pointer rounded-lg px-3 py-2 text-sm font-medium transition-all
					{p === currentPage
						? ''
						: 'text-[var(--color-text-muted)] hover:bg-[var(--color-primary-subtle)]'}"
				style={p === currentPage ? 'background: var(--color-primary); color: var(--color-primary-fg);' : ''}
				>
					{p}
				</button>
			{/each}
			<button
				onclick={() => goToPage(currentPage + 1)}
				disabled={currentPage >= totalPages}
				class="cursor-pointer rounded-lg px-3 py-2 text-sm text-[var(--color-text-muted)]
					hover:bg-[var(--color-primary-subtle)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
			>
				→
			</button>
		</div>
	{/if}
{/if}

<style>
	.source-btn-inactive:hover {
		color: var(--color-text);
		box-shadow: 0 3px 10px rgba(0,0,0,0.15) !important;
	}
	.source-btn-active:hover {
		box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
	}
</style>
