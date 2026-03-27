<script lang="ts">
	import './layout.css';
	import { browser } from '$app/environment';

	let { children } = $props();

	let toastMessage = $state('');
	let toastVisible = $state(false);
	let dark = $state(false);

	// Initialize dark state from DOM (already set by app.html blocking script)
	$effect(() => {
		if (browser) {
			dark = document.documentElement.classList.contains('dark');
		}
	});

	// Sync dark class to document
	$effect(() => {
		if (browser) {
			document.documentElement.classList.toggle('dark', dark);
		}
	});

	function toggleDark() {
		dark = !dark;
		localStorage.setItem('theme', dark ? 'dark' : 'light');
	}

	function showToast(msg: string) {
		toastMessage = msg;
		toastVisible = true;
		setTimeout(() => { toastVisible = false; }, 1500);
	}
</script>

<svelte:head>
	<title>Microsoft News</title>
</svelte:head>

<div class="min-h-screen bg-[var(--color-bg)] transition-colors duration-300">
	<header class="sticky top-0 z-50 bg-[var(--color-surface)]/90 backdrop-blur-xl border-b-2 border-[var(--color-border-strong)]">
		<div class="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
			<a href="/" class="group">
				<img src={dark ? '/logo-dark.svg' : '/logo.svg'} alt="Microsoft News" class="h-6 group-hover:opacity-70 transition-opacity" />
			</a>
			<nav class="flex items-center gap-1">
				<button
					onclick={() => showToast('추후 제공 예정입니다')}
					class="rounded-lg px-3 py-1.5 text-[13px] text-[var(--color-text-muted)]
						hover:text-[var(--color-text)] hover:bg-[var(--color-primary-subtle)] active:scale-95 transition-all cursor-pointer"
				>
					Dashboard
				</button>
				<button
					onclick={() => showToast('추후 제공 예정입니다')}
					class="rounded-lg px-3 py-1.5 text-[13px] text-[var(--color-text-muted)]
						hover:text-[var(--color-text)] hover:bg-[var(--color-primary-subtle)] active:scale-95 transition-all cursor-pointer"
				>
					Newsletter
				</button>
				<button
					onclick={toggleDark}
					class="ml-1 rounded-lg p-1.5 text-[var(--color-text-subtle)]
						hover:text-[var(--color-text)] hover:bg-[var(--color-primary-subtle)] active:scale-95 transition-all cursor-pointer"
					aria-label="Toggle dark mode"
				>
					{#if dark}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m8.66-13.66l-.71.71M4.05 19.95l-.71.71M21 12h-1M4 12H3m16.66 7.66l-.71-.71M4.05 4.05l-.71-.71M16 12a4 4 0 11-8 0 4 4 0 018 0z"/></svg>
					{:else}
						<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>
					{/if}
				</button>
			</nav>
		</div>
	</header>

	<main class="mx-auto max-w-7xl px-6 py-10">
		{@render children()}
	</main>

	<!-- Toast -->
	{#if toastVisible}
		<div class="fixed bottom-8 inset-x-0 z-[100] flex justify-center pointer-events-none animate-[toast-in_0.25s_ease-out]">
		<div class="rounded-lg px-5 py-2.5 text-sm shadow-lg pointer-events-auto"
			style="background: var(--color-toast-bg); color: var(--color-toast-text);">
			{toastMessage}
		</div>
		</div>
	{/if}

	<footer class="mt-16">
		<div class="mx-auto max-w-7xl px-6 py-6 flex items-center justify-between border-t-2 border-[var(--color-border-strong)]">
			<span class="text-xs text-[var(--color-text-subtle)]">Microsoft News</span>
			<div class="flex items-center gap-1.5">
				<span class="h-1.5 w-1.5 rounded-full bg-[var(--color-status-active)] animate-pulse"></span>
				<span class="text-[11px] text-[var(--color-text-subtle)]">Syncing</span>
			</div>
		</div>
	</footer>
</div>
