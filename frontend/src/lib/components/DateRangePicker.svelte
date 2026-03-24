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
</script>

<input
	bind:this={inputEl}
	type="text"
	placeholder="날짜 범위 선택"
	readonly
	class="box-border w-full rounded-lg bg-white px-3 text-sm cursor-pointer
		focus:ring-1 focus:ring-[var(--color-primary)] focus:outline-none"
	style="height: 42px; line-height: 42px; box-shadow: 0 1px 6px rgba(0,0,0,0.14); border: none;"
/>

<style>
	:global(.flatpickr-calendar) {
		font-size: 13px;
	}
</style>
