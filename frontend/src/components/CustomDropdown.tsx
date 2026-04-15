import React, { useState, useMemo } from 'react';
import { View, Text, TouchableOpacity, ScrollView, TextInput, StyleSheet } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { THEME } from '../utils/constants';
import AppIcon from './AppIcon';

interface CustomDropdownProps {
  data: readonly string[] | readonly number[] | string[] | number[];
  selectedValue: string | number | null | undefined;
  onSelect: (val: any) => void;
  placeholder?: string;
  searchable?: boolean;
}

const CustomDropdown: React.FC<CustomDropdownProps> = ({
  data,
  selectedValue,
  onSelect,
  placeholder = "Wybierz...",
  searchable = false
}) => {
  const { colors } = useTheme();
  const styles = useMemo(() => getStyles(colors), [colors]);

  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredData = useMemo(() => {
    if (!searchable || !searchQuery) return data;
    return data.filter(item =>
      String(item).toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [data, searchable, searchQuery]);

  return (
    <View style={styles.dropdownContainer}>
      <TouchableOpacity
        style={styles.dropdownButton}
        onPress={() => setIsOpen(!isOpen)}
      >
        <Text style={[styles.input, styles.dropdownInputText]}>
          {selectedValue ? String(selectedValue) : placeholder}
        </Text>
        <AppIcon name="ArrowDown" size={24} />
      </TouchableOpacity>

      {isOpen && (
        <View style={styles.dropdownList}>
          {searchable && (
            <TextInput
              style={styles.searchInput}
              placeholder="Szukaj..."
              placeholderTextColor={colors.searchWord}
              value={searchQuery}
              onChangeText={setSearchQuery}
            />
          )}
          <ScrollView nestedScrollEnabled style={{ maxHeight: 200 }}>
            {filteredData.map((item, index) => (
              <TouchableOpacity
                key={index.toString()}
                style={styles.dropdownItem}
                onPress={() => {
                  onSelect(item);
                  setIsOpen(false);
                  setSearchQuery("");
                }}
              >
                <Text style={styles.dropdownItemText}>{String(item)}</Text>
              </TouchableOpacity>
            ))}
            {filteredData.length === 0 && (
              <View style={styles.dropdownItem}>
                <Text style={styles.dropdownItemText}>Brak wyników</Text>
              </View>
            )}
          </ScrollView>
        </View>
      )}
    </View>
  );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
  dropdownContainer: {
    position: 'relative',
    zIndex: 10,
  },
  dropdownButton: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: THEME.borderRadius.m,
    backgroundColor: colors.background,
    paddingRight: THEME.spacing.s,
  },
  dropdownInputText: {
    flex: 1,
    borderWidth: 0,
    backgroundColor: 'transparent',
  },
  input: {
    ...THEME.typography.text,
    padding: THEME.spacing.m,
    color: colors.text,
  },
  dropdownList: {
    marginTop: THEME.spacing.xs,
    backgroundColor: colors.background,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: THEME.borderRadius.m,
    overflow: 'hidden',
  },
  searchInput: {
    ...THEME.typography.text,
    padding: THEME.spacing.m,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    color: colors.text,
  },
  dropdownItem: {
    padding: THEME.spacing.m,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  dropdownItemText: {
    ...THEME.typography.text,
    color: colors.text,
  }
});

export default CustomDropdown;
