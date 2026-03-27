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
		--border-focused="none"
		--background="var(--color-surface)"
		--list-background="var(--color-surface)"
		--list-border="none"
		--list-border-radius="0.5rem"
		--list-shadow="var(--shadow-lg)"
		--item-hover-bg="var(--color-primary-subtle)"
		--item-is-active-bg="var(--color-primary-muted)"
		--item-is-active-color="var(--color-text)"
		--font-size="0.875rem"
		--height="44px"
		--padding="0 8px 0 12px"
		--placeholder-color="var(--color-text-muted)"
		--chevron-color="var(--color-text-muted)"
		--clear-icon-color="var(--color-text-muted)"
	/>
</div>

<style>
	.filter-select {
		min-width: 0;
		box-shadow: none;
		border-radius: 0.5rem;
		border: 1px solid var(--color-border);
		cursor: pointer;
	}
	.filter-select:focus-within {
		outline: 2px solid var(--color-primary);
		outline-offset: -1px;
	}
	.filter-select :global(.svelte-select) {
		cursor: pointer;
	}
	.filter-select :global(.svelte-select input) {
		cursor: pointer;
	}
</style>
