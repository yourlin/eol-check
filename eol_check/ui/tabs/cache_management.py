"""
Cache Management tab for the End of Life Checker UI.
"""

import os
import streamlit as st

from eol_check.utils.cache import Cache
from eol_check.ui.utils.cache_utils import load_cache_data


def render_cache_management_tab():
    """Render the Cache Management tab."""
    st.header("Cache Management")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Cached Data")
        cache = Cache()
        cache_dir = cache.cache_dir
        st.info(f"Cache directory: {cache_dir}")

        refresh_cache = st.button("Refresh Cache Data", key="refresh_cache_button")

        if refresh_cache or "cache_data" not in st.session_state:
            with st.spinner("Loading cache data..."):
                st.session_state.cache_data = load_cache_data()
                # Reset filter to "All" when refreshing
                if "cache_filter" in st.session_state:
                    st.session_state.cache_filter = 0

        # Display cache data
        if st.session_state.get("cache_data"):
            # Filter options
            filter_options = [
                "All",
                "Valid",
                "Expired",
                "Not Found",
            ]
            selected_filter = st.selectbox("Filter by Status", filter_options, key="cache_filter")
            
            # Apply filters
            if selected_filter == "Valid":
                filtered_data = [item for item in st.session_state.cache_data if not item["is_expired"] and item["content"] != "Empty (Not Found)"]
            elif selected_filter == "Expired":
                filtered_data = [item for item in st.session_state.cache_data if item["is_expired"]]
            elif selected_filter == "Not Found":
                filtered_data = [item for item in st.session_state.cache_data if item["content"] == "Empty (Not Found)"]
            else:  # All
                filtered_data = st.session_state.cache_data
            
            # Create a dataframe for display
            if filtered_data:
                # Add a help tooltip for the Expires column
                st.markdown("**Note:** 'Cache Expiry' shows when the cached data will expire and need to be refreshed from the API.")
                
                cache_table = []
                for item in filtered_data:
                    # Determine status based on content and expiry
                    if item["content"] == "Empty (Not Found)":
                        status = "Not Found"
                        status_emoji = "❓"
                    elif item["is_expired"]:
                        status = "Expired"
                        status_emoji = "⏱️"
                    else:
                        status = "Valid"
                        status_emoji = "✅"
                    
                    # Extract just the package name from the key
                    package_name = item["key"].split("/")[-1] if "/" in item["key"] else item["key"]
                    
                    # Handle expires date for not found items
                    expires_date = item["expires_at"] if item["content"] != "Empty (Not Found)" else item["expires_at"]
                    
                    cache_table.append({
                        "Status": f"{status_emoji} {status}",
                        "Package": package_name,
                        "Content": item["content"],
                        "Cache Expiry": expires_date,
                    })
                
                st.dataframe(
                    cache_table, 
                    use_container_width=True
                )
                
                st.text(f"Total: {len(filtered_data)} items")
        else:
            st.info("No cache data available.")

    with col2:
        st.subheader("Cache Actions")

        # Clear cache button
        if st.button("Clear All Cache", type="secondary", key="clear_cache_button"):
            try:
                cache = Cache()
                cache.clear()
                st.success("Cache cleared successfully!")
                # Reset cache data in session state
                if "cache_data" in st.session_state:
                    del st.session_state.cache_data
                # Force refresh
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error clearing cache: {e}")

        # Clear expired cache
        if st.button("Clear Expired Cache"):
            try:
                count = 0
                for item in st.session_state.get("cache_data", []):
                    if item["is_expired"] and os.path.exists(item["file_path"]):
                        os.remove(item["file_path"])
                        count += 1

                if count > 0:
                    st.success(f"Cleared {count} expired cache items!")
                    # Reset session state to force refresh
                    if "cache_data" in st.session_state:
                        del st.session_state.cache_data
                else:
                    st.info("No expired cache items to clear.")
            except Exception as e:
                st.error(f"Error clearing expired cache: {e}")
