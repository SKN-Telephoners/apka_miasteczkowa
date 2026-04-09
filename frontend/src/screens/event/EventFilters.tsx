import React, { useMemo, useState } from "react";
import { SafeAreaView, StyleSheet, Text, View, TouchableOpacity, ScrollView } from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { THEME } from "../../utils/constants";
import {
  DEFAULT_EVENT_FILTERS,
  EventCreatedAtFilter,
  EventCreatorFilter,
  EventFilterState,
  EventParticipationFilter,
  EventVisibilityFilter,
  FutureEventSortMode,
} from "../../types";

type FilterOption<T extends string> = {
  label: string;
  value: T;
  disabled?: boolean;
};

const visibilityOptions: FilterOption<EventVisibilityFilter>[] = [
  { label: "Wszystkie", value: "all" },
  { label: "Publiczne", value: "public" },
  { label: "Prywatne", value: "private" },
];

const creatorOptions: FilterOption<EventCreatorFilter>[] = [
  { label: "Wszyscy", value: "all" },
  { label: "Od znajomych", value: "friends", disabled: true },
  { label: "Od innych", value: "others", disabled: true },
];

const participationOptions: FilterOption<EventParticipationFilter>[] = [
  { label: "Wszystkie", value: "all" },
  { label: "Dołączono", value: "joined" },
  { label: "Nie dołączono", value: "not_joined" },
];

const sortOptions: FilterOption<FutureEventSortMode>[] = [
  { label: "Domyślne", value: "default" },
  { label: "Najwięcej członków", value: "members_desc" },
  { label: "Najmniej członków", value: "members_asc" },
  { label: "Najwięcej komentarzy", value: "comments_desc" },
  { label: "Najmniej komentarzy", value: "comments_asc" },
];

const addedWhenOptions: FilterOption<EventCreatedAtFilter>[] = [
  { label: "Wszystkie", value: "all" },
  { label: "Dodane dzisiaj", value: "today" },
  { label: "W tym tygodniu", value: "week" },
  { label: "W tym miesiącu", value: "month" },
  { label: "W tym roku", value: "year" },
  { label: "Starsze", value: "older" },
];

const EventFilters = () => {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const initialFilters = route?.params?.initialFilters as EventFilterState | undefined;
  const [filters, setFilters] = useState<EventFilterState>(initialFilters ?? DEFAULT_EVENT_FILTERS);
  const [openDropdown, setOpenDropdown] = useState<"sort" | "added" | null>(null);

  const creatorSectionHint = useMemo(
    () => "Opcje znajomi/inni są przygotowane i jeszcze nieaktywne.",
    []
  );

  const applyFilters = () => {
    navigation.navigate({
      name: "EventScreen",
      params: { eventFilters: filters },
      merge: true,
    });
  };

  const resetFilters = () => {
    setFilters(DEFAULT_EVENT_FILTERS);
    setOpenDropdown(null);
  };

  const renderDropdown = <T extends string>(
    title: string,
    value: T,
    options: FilterOption<T>[],
    keyName: "sort" | "added",
    onSelect: (next: T) => void
  ) => {
    const selectedLabel = options.find((option) => option.value === value)?.label ?? "Wybierz";
    const isOpen = openDropdown === keyName;

    return (
      <View style={styles.dropdownSection}>
        <Text style={styles.sectionTitle}>{title}</Text>
        <TouchableOpacity
          style={styles.dropdownButton}
          activeOpacity={0.85}
          onPress={() => setOpenDropdown((prev) => (prev === keyName ? null : keyName))}
        >
          <Text style={styles.dropdownButtonText}>{selectedLabel}</Text>
          <Text style={styles.dropdownChevron}>{isOpen ? "▲" : "▼"}</Text>
        </TouchableOpacity>

        {isOpen && (
          <View style={styles.dropdownMenu}>
            {options.map((option) => {
              const selected = option.value === value;
              return (
                <TouchableOpacity
                  key={option.value}
                  style={[styles.dropdownItem, selected && styles.dropdownItemSelected]}
                  activeOpacity={0.85}
                  onPress={() => {
                    onSelect(option.value);
                    setOpenDropdown(null);
                  }}
                >
                  <Text style={[styles.dropdownItemText, selected && styles.dropdownItemTextSelected]}>
                    {option.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
      </View>
    );
  };

  const renderOptionRow = <T extends string>(
    options: FilterOption<T>[],
    selectedValue: T,
    onSelect: (value: T) => void
  ) => {
    return (
      <View style={styles.optionsWrap}>
        {options.map((option) => {
          const selected = selectedValue === option.value;
          const disabled = Boolean(option.disabled);

          return (
            <TouchableOpacity
              key={option.value}
              style={[
                styles.optionButton,
                selected && styles.optionButtonSelected,
                disabled && styles.optionButtonDisabled,
              ]}
              activeOpacity={0.85}
              onPress={() => !disabled && onSelect(option.value)}
              disabled={disabled}
            >
              <Text
                style={[
                  styles.optionText,
                  selected && styles.optionTextSelected,
                  disabled && styles.optionTextDisabled,
                ]}
              >
                {option.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>Filtrowanie wydarzen</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Typ wydarzenia</Text>
          {renderOptionRow(visibilityOptions, filters.visibility, (value) => {
            setFilters((prev) => ({ ...prev, visibility: value }));
          })}
        </View>

        {renderDropdown("Sortuj", filters.sortMode, sortOptions, "sort", (value) => {
          setFilters((prev) => ({ ...prev, sortMode: value }));
        })}

        {renderDropdown("Kiedy dodano", filters.createdAtWindow, addedWhenOptions, "added", (value) => {
          setFilters((prev) => ({ ...prev, createdAtWindow: value }));
        })}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Kto</Text>
          {renderOptionRow(creatorOptions, filters.creatorSource, (value) => {
            setFilters((prev) => ({ ...prev, creatorSource: value }));
          })}
          <Text style={styles.hint}>{creatorSectionHint}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Udział</Text>
          {renderOptionRow(participationOptions, filters.participation, (value) => {
            setFilters((prev) => ({ ...prev, participation: value }));
          })}
        </View>

        <View style={styles.actionsRow}>
          <TouchableOpacity style={styles.secondaryButton} onPress={resetFilters} activeOpacity={0.85}>
            <Text style={styles.secondaryButtonText}>Wyczyść</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.primaryButton} onPress={applyFilters} activeOpacity={0.85}>
            <Text style={styles.primaryButtonText}>Zastosuj</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: THEME.colors.lm_bg,
  },
  container: {
    paddingTop: 20,
    paddingBottom: 30,
    paddingHorizontal: 20,
  },
  title: {
    ...THEME.typography.eventTitle,
    marginBottom: 16,
  },
  section: {
    marginBottom: 18,
  },
  dropdownSection: {
    marginBottom: 18,
  },
  sectionTitle: {
    ...THEME.typography.title,
    marginBottom: 10,
    color: THEME.colors.lm_txt,
  },
  dropdownButton: {
    borderWidth: 1,
    borderColor: THEME.colors.lm_ico,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: THEME.colors.lm_bg,
  },
  dropdownButtonText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
  },
  dropdownChevron: {
    ...THEME.typography.text,
    color: THEME.colors.lm_ico,
    marginLeft: 12,
  },
  dropdownMenu: {
    borderWidth: 1,
    borderColor: THEME.colors.lm_ico,
    borderRadius: 12,
    marginTop: 8,
    overflow: "hidden",
  },
  dropdownItem: {
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: THEME.colors.lm_bg,
  },
  dropdownItemSelected: {
    backgroundColor: "rgba(245, 146, 69, 0.16)",
  },
  dropdownItemText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
  },
  dropdownItemTextSelected: {
    fontWeight: "700",
  },
  optionsWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  optionButton: {
    borderWidth: 1,
    borderColor: THEME.colors.lm_ico,
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: THEME.colors.lm_bg,
  },
  optionButtonSelected: {
    borderColor: THEME.colors.transparentOrange,
    backgroundColor: "rgba(245, 146, 69, 0.16)",
  },
  optionButtonDisabled: {
    opacity: 0.5,
  },
  optionText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_ico,
  },
  optionTextSelected: {
    color: THEME.colors.lm_txt,
    fontWeight: "700",
  },
  optionTextDisabled: {
    color: THEME.colors.lm_ico,
  },
  hint: {
    ...THEME.typography.text,
    color: THEME.colors.lm_ico,
    marginTop: 8,
  },
  actionsRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 10,
    marginTop: 6,
  },
  secondaryButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: THEME.colors.lm_ico,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
  },
  primaryButton: {
    flex: 1,
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
    backgroundColor: THEME.colors.transparentOrange,
  },
  secondaryButtonText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
    fontWeight: "700",
  },
  primaryButtonText: {
    ...THEME.typography.text,
    color: "#fff",
    fontWeight: "700",
    textAlign: "center",
  },
});

export default EventFilters;
