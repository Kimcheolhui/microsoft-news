<script lang="ts">
	import flatpickr from 'flatpickr';
	import { Korean } from 'flatpickr/dist/l10n/ko.js';
	import 'flatpickr/dist/flatpickr.min.css';
	import { onMount } from 'svelte';

	interface Props {
		dateFrom: string;
		dateTo: string;
		onchange: (from: string, to: string) => void;
	}

	let { dateFrom, dateTo, onchange }: Props = $props();

	let inputEl: HTMLInputElement;
	let fp: flatpickr.Instance;

	function fmt(d: Date): string {
		const y = d.getFullYear();
		const m = String(d.getMonth() + 1).padStart(2, '0');
		const day = String(d.getDate()).padStart(2, '0');
		return `${y}-${m}-${day}`;
	}

	onMount(() => {
		fp = flatpickr(inputEl, {
			mode: 'range',
			locale: Korean,
			dateFormat: 'Y-m-d',
			allowInput: true,
			defaultDate: dateFrom && dateTo ? [dateFrom, dateTo] : undefined,
			onChange(selectedDates) {
				if (selectedDates.length === 2) {
					onchange(fmt(selectedDates[0]), fmt(selectedDates[1]));
				} else if (selectedDates.length === 0) {
					onchange('', '');
				}
			}
		});

		return () => fp?.destroy();
	});

	export function clear() {
		fp?.clear();
	}

	export function setDates(from: string, to: string) {
		if (from && to) {
			fp?.setDate([from, to], false);
		} else {
			fp?.clear();
		}
	}
</script>

<input
	bind:this={inputEl}
	type="text"
	placeholder="Date Range"
	readonly
	class="box-border w-full rounded-lg bg-[var(--color-surface)] px-3 text-sm text-[var(--color-text)] cursor-pointer
		focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none"
	style="height: 44px; line-height: 44px; border: 1px solid var(--color-border);"
/>

<style>
	:global(.flatpickr-calendar) {
		font-size: 13px;
	}
</style>
