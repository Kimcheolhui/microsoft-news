<script lang="ts">
	import Select from 'svelte-select';

	interface Option {
		value: string;
		label: string;
	}

	interface Props {
		options: Option[];
		value: string;
		placeholder?: string;
		onchange?: (value: string) => void;
	}

	let { options, value = $bindable(''), placeholder = '선택...', onchange }: Props = $props();

	let selected: Option | undefined = $derived(
		value ? options.find((o) => o.value === value) : undefined
	);

	function handleChange(e: CustomEvent<Option>) {
		value = e.detail?.value ?? '';
		onchange?.(value);
	}

	function handleClear() {
		value = '';
		onchange?.('');
	}
</script>

<div class="filter-select">
	<Select
		items={options}
		value={selected}
		on:change={handleChange}
		on:clear={handleClear}
		itemId="value"
		label="label"
		{placeholder}
		showChevron
		clearable
		searchable={false}
		--border-radius="0.5rem"
		--border="none"
		--border-hover="none"
		--border-focused="1px solid var(--color-primary)"
		--background="#fff"
		--list-background="#fff"
		--list-border="none"
		--list-border-radius="0.5rem"
		--list-shadow="0 4px 12px rgba(0,0,0,0.1)"
		--item-hover-bg="rgba(0,120,212,0.06)"
		--item-is-active-bg="rgba(0,120,212,0.1)"
		--item-is-active-color="var(--color-text)"
		--font-size="0.875rem"
		--height="36px"
		--padding="0 8px 0 12px"
		--placeholder-color="var(--color-text-muted)"
		--chevron-color="var(--color-text-muted)"
		--clear-icon-color="var(--color-text-muted)"
	/>
</div>

<style>
	.filter-select {
		min-width: 0;
		box-shadow: 0 1px 6px rgba(0, 0, 0, 0.14);
		border-radius: 0.5rem;
	}
</style>
