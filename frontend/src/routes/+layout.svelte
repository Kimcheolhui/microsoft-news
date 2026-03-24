<script lang="ts">
	import './layout.css';

	let { children } = $props();
</script>

<svelte:head>
	<title>Azure News</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)]">
	<header class="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
		<div class="mx-auto max-w-6xl px-4 py-4 flex items-center gap-3">
			<a href="/" class="text-xl font-bold text-[var(--color-primary)] hover:opacity-80">
				Azure News
			</a>
			<span class="text-sm text-[var(--color-text-muted)]">업데이트 & 분석 리포트</span>
		</div>
	</header>

	<main class="mx-auto max-w-6xl px-4 py-6">
		{@render children()}
	</main>
</div>
